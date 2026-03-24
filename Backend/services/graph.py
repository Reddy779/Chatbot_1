import os
import asyncio
import traceback
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from models.schemas import AgentState
from services.prompts import (
    build_system_prompt,
    SUPERVISOR_PROMPT,
    RESEARCH_AGENT_PROMPT,
    TOOL_AGENT_PROMPT,
    FACT_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
)
from services.tools import RESEARCH_TOOLS, TOOL_AGENT_TOOLS
from services.memory import (
    get_recent_messages,
    get_recent_summaries,
    get_user_facts,
    get_message_count,
    ensure_user_and_session,
    save_message_pair,
    save_user_facts,
    save_summary,
    parse_facts_from_llm,
)

load_dotenv()

# LLM 
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    temperature=0.7,
    max_tokens=1024,
    streaming=True
)

llm_supervisor = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_tokens=15, 
    streaming=False,
)

llm_small = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_tokens=512,
    streaming=False,
)

llm_research = llm.bind_tools(RESEARCH_TOOLS)
llm_tool     = llm.bind_tools(TOOL_AGENT_TOOLS)


# NODE 1 [ Memory Retrieval Node]
async def memory_retrieval_node(state: AgentState) -> dict:
    """
    Fetches all memory layers from Neon before the LLM call.
    Does NOT stream anything — purely a DB read node.
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        history       = await get_recent_messages(db, state.session_id)
        summaries     = await get_recent_summaries(db, state.user_id)
        user_facts    = await get_user_facts(db, state.user_id)
        message_count = await get_message_count(db, state.session_id)

    except Exception as e:
        traceback.print_exc()
        print(f"Memory retrieval error: {e}")
        history, summaries, user_facts, message_count = [], [], [], 0
    finally:
        await db.close()

    print(f"Retrieved: {len(history)} messages, "
          f"{len(summaries)} summaries, {len(user_facts)} facts")

    return {
        "history":       history,
        "summaries":     summaries,
        "user_facts":    user_facts,
        "message_count": message_count,
    }


# NODE 2 [ supervisor_node ]
async def supervisor_node(state: AgentState) -> dict:
    """
    Reads the user's latest message and decides which agent handles it.
    Outputs one of: chat_agent, research_agent, tool_agent.

    Uses llm_supervisor (8B model, temp=0, max_tokens=15) because:
    - We only need a single word output — small model is faster
    - temp=0 gives deterministic routing — same input always routes same way
    - max_tokens=10 is enough for the longest option "research_agent"
    """

    user_message = state.messages[-1].content

    prompt = SUPERVISOR_PROMPT.format(message=user_message)

    try:
        response = await llm_supervisor.ainvoke(prompt)
        decision = response.content.strip().lower()

        # Validate the decision — if unexpected output, default to chat_agent
        valid_agents = {"chat_agent", "research_agent", "tool_agent"}
        if decision not in valid_agents:
            print(f"Supervisor gave unexpected output: '{decision}' — defaulting to chat_agent")
            decision = "chat_agent"

    except Exception as e:
        print(f"Supervisor failed: {e} — defaulting to chat_agent")
        decision = "chat_agent"

    print(f"Supervisor routed to: {decision}")
    return {"next_agent": decision}


# NODE 3 [ Chat Agent Node ]
async def chat_agent_node(state: AgentState) -> dict:
    """
    Default agent — handles general conversation.
    Most memory-aware of the three agents.
    Uses full personalized system prompt with facts and summaries.
    """
    system_prompt = build_system_prompt(
        user_facts=state.user_facts,
        summaries=state.summaries,
    )

    history_messages = []
    for msg in state.history:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        else:
            history_messages.append(AIMessage(content=msg["content"]))

    all_messages = (
        [SystemMessage(content=system_prompt)]
        + history_messages
        + state.messages
    )

    response = await llm.ainvoke(all_messages)
    print(f"💬 chat_agent responded: {response.content[:80]}...")
    return {"messages": [response]}


# NODE 4 [ Research Agent Node ]
async def research_agent_node(state: AgentState) -> dict:
    """
    Research agent — handles web search and information synthesis.
    Has web_search_tool bound to it.
    Uses multi-step reasoning: search → observe results → respond.
    """
    all_messages = (
        [SystemMessage(content=RESEARCH_AGENT_PROMPT)]
        + state.messages
    )

    response = await llm_research.ainvoke(all_messages)

    # If the LLM wants to call a tool, tool_calls will be populated
    if response.tool_calls:
        print(f"research_agent calling tool: {response.tool_calls[0]['name']}")
    else:
        print(f"research_agent responded: {response.content[:80]}...")

    return {"messages": [response]}


# NODE 5 [ Tool Agent Node ]
async def tool_agent_node(state: AgentState) -> dict:
    """
    Tool agent — handles calculations, weather, and API lookups.
    Has calculator_tool and weather_tool bound to it.
    """
    all_messages = (
        [SystemMessage(content=TOOL_AGENT_PROMPT)]
        + state.messages
    )

    response = await llm_tool.ainvoke(all_messages)

    if response.tool_calls:
        print(f"tool_agent calling tool: {response.tool_calls[0]['name']}")
    else:
        print(f"tool_agent responded: {response.content[:80]}...")

    return {"messages": [response]}


# NODE 6 [ Memory Writer Node ]
async def memory_writer_node(state: AgentState) -> dict:
    """
    Saves messages, extracts facts, summarizes if needed.
    Does NOT stream anything — purely a DB write node.
    Runs after chat_node finishes, so the full reply is available.
    """
    from main import db_session_factory

    assistant_reply = state.messages[-1].content
    user_message = (
        state.messages[-2].content
        if len(state.messages) >= 2
        else state.messages[0].content
    )

    db = db_session_factory()
    try:
        # Job 1: Ensure user/session rows exist, save messages 
        await ensure_user_and_session(db, state.user_id, state.session_id)
        await save_message_pair(
            db, state.session_id, user_message, assistant_reply
        )
        print(f"Saved message pair for session {state.session_id}")

        # Job 2: Extract new user facts 
        conversation_text = (
            f"User: {user_message}\nAssistant: {assistant_reply}"
        )
        fact_prompt = FACT_EXTRACTION_PROMPT.format(
            conversation=conversation_text,
            existing_facts=state.user_facts,
        )

        try:
            fact_response = await llm_small.ainvoke(fact_prompt)
            new_facts = parse_facts_from_llm(fact_response.content)
            if new_facts:
                await save_user_facts(
                    db, state.user_id, new_facts, state.user_facts
                )
                print(f"Saved {len(new_facts)} new facts: {new_facts}")
            else:
                print("No new facts extracted")
        except Exception as e:
            print(f"Fact extraction failed: {e}")

        # Job 3: Summarize if session is long enough 
        new_count = state.message_count + 2
        if new_count >= 30 and new_count % 30 == 0:
            try:
                history_text = "\n".join([
                    f"{m['role'].title()}: {m['content']}"
                    for m in state.history
                ])
                summary_prompt = SUMMARY_PROMPT.format(
                    conversation=history_text
                )
                summary_response = await llm_small.ainvoke(summary_prompt)
                await save_summary(
                    db, state.session_id, summary_response.content
                )
                print(f" Summary saved for session {state.session_id}")
            except Exception as e:
                print(f" Summarization failed: {e}")

    except Exception as e:
        traceback.print_exc()
        print(f"Memory writer error: {e}")
    finally:
        await db.close()   

    return {}


# ROUTING FUNCTION
def route_to_agent(state: AgentState) -> str:
    """
    This function is used as the conditional edge after supervisor_node.
    LangGraph calls this function and uses the return value to decide
    which node to execute next.

    It simply reads next_agent from state and returns it.
    LangGraph maps the return value to the actual node name.
    """
    return state.next_agent


# GRAPH
def build_graph(checkpointer):
    """
    START → memory_retrieval → supervisor
    supervisor → chat_agent | research_agent | tool_agent  (conditional)
    all agents → tool_node (if tool call needed) → back to agent
    all agents → memory_writer → END
    """
    graph = StateGraph(AgentState)

    research_tool_node = ToolNode(RESEARCH_TOOLS)
    tool_agent_tool_node = ToolNode(TOOL_AGENT_TOOLS)

    graph.add_node("memory_retrieval",    memory_retrieval_node)
    graph.add_node("supervisor",          supervisor_node)
    graph.add_node("chat_agent",          chat_agent_node)
    graph.add_node("research_agent",      research_agent_node)
    graph.add_node("research_tools",      research_tool_node)
    graph.add_node("tool_agent",          tool_agent_node)
    graph.add_node("tool_agent_tools",    tool_agent_tool_node)
    graph.add_node("memory_writer",       memory_writer_node)

# Fixed edges
    graph.add_edge(START,              "memory_retrieval")
    graph.add_edge("memory_retrieval", "supervisor")

# Conditional edge from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "chat_agent":     "chat_agent",
            "research_agent": "research_agent",
            "tool_agent":     "tool_agent",
        }
    )
# Tool loop for research_agent
    graph.add_conditional_edges(
        "research_agent",
        lambda state: "research_tools"
            if state.messages[-1].tool_calls
            else "memory_writer",
        {
            "research_tools": "research_tools",
            "memory_writer":  "memory_writer",
        }
    )

    graph.add_edge("research_tools", "research_agent")

# Tool loop for tool_agent
    graph.add_conditional_edges(
        "tool_agent",
        lambda state: "tool_agent_tools"
            if state.messages[-1].tool_calls
            else "memory_writer",
        {
            "tool_agent_tools": "tool_agent_tools",
            "memory_writer":    "memory_writer",
        }
    )

    graph.add_edge("tool_agent_tools", "tool_agent")

    graph.add_edge("chat_agent",   "memory_writer")
    graph.add_edge("memory_writer", END)

    return graph.compile(checkpointer=checkpointer)