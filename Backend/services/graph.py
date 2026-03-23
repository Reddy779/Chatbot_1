import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from models.schemas import AgentState

load_dotenv()

# ── LLM 
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    temperature=0.7,
    max_tokens=1024,
)

# ── Node 
async def chat_node(state: AgentState) -> dict:
    response = await llm.ainvoke(state.messages)
    return {"messages": [response]}

# ── Graph builder 
def build_graph(checkpointer):
    graph = StateGraph(AgentState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)
    return graph.compile(checkpointer=checkpointer)