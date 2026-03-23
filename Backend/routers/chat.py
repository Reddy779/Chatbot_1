from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage

from models.schemas import ChatRequest, ChatResponse
from services.graph import llm

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):

    graph = req.app.extra.get("graph") or req.app.state.__dict__.get("graph")

    from main import app_state
    graph = app_state["graph"]

    config = {"configurable": {"thread_id": request.session_id}}

    initial_state = {
        "messages":   [HumanMessage(content=request.message)],
        "user_id":    request.user_id,
        "session_id": request.session_id,
        "user_facts": [],
        "summaries":  [],
    }

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Graph error: {str(e)}")

    reply = result["messages"][-1].content

    return ChatResponse(
        session_id=request.session_id,
        user_id=request.user_id,
        reply=reply,
        model=llm.model_name,
    )