import os
import asyncio
import traceback
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from models.schemas import AgentState
from services.prompts import (
    build_system_prompt,
    FACT_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
)
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
)

llm_small = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_tokens=512,
)


# NODE 1 — memory_retrieval_node
async def memory_retrieval_node(state: AgentState) -> dict:
    """
    Runs first on every request.
    Fetches all memory layers sequentially — asyncio.gather causes
    conflicts when multiple queries share the same session.
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


# NODE 2 — chat_node
async def chat_node(state: AgentState) -> dict:
    """
    Builds rich system prompt from memory and calls the LLM.
    No DB access here — only LLM call.
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
    print(f"LLM responded: {response.content[:80]}...")

    return {"messages": [response]}


# NODE 3 — memory_writer_node
async def memory_writer_node(state: AgentState) -> dict:
    """
    Runs last on every request.
    Opens its own fresh DB session, does all writes, closes cleanly.
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
        print(f" Memory writer error: {e}")
    finally:
        await db.close()   

    return {}


# GRAPH
def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("memory_retrieval", memory_retrieval_node)
    graph.add_node("chat_node",        chat_node)
    graph.add_node("memory_writer",    memory_writer_node)

    graph.add_edge(START,              "memory_retrieval")
    graph.add_edge("memory_retrieval", "chat_node")
    graph.add_edge("chat_node",        "memory_writer")
    graph.add_edge("memory_writer",    END)

    return graph.compile(checkpointer=checkpointer)