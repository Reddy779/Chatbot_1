import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(request: ChatRequest):

    from main import app_state

    graph = app_state["graph"]
    if not graph:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable — graph not initialized."
        )

    config = {"configurable": {"thread_id": request.session_id}}

    initial_state = {
        "messages":      [HumanMessage(content=request.message)],
        "user_id":       request.user_id,
        "session_id":    request.session_id,
        "user_facts":    [],
        "summaries":     [],
        "history":       [],
        "message_count": 0,
    }

    async def event_stream():
        try:
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v2",
            ):
                event_type = event.get("event", "")

                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")

                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = json.dumps({"chunk": chunk.content})
                        yield f"data: {payload}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            traceback.print_exc()
            error_str = str(e)

            # Groq rate limit — return 429 with retry message
            if "rate_limit" in error_str.lower() or "429" in error_str:
                yield f"data: {json.dumps({'error': 'Rate limit reached. Please wait a moment and try again.', 'code': 429})}\n\n"

            # Tool timeout
            elif "timeout" in error_str.lower():
                yield f"data: {json.dumps({'error': 'Request timed out. Please try again.', 'code': 504})}\n\n"

            # DB failure
            elif "database" in error_str.lower() or "connection" in error_str.lower():
                yield f"data: {json.dumps({'error': 'Database temporarily unavailable. Please try again.', 'code': 503})}\n\n"

            # Generic error
            else:
                yield f"data: {json.dumps({'error': f'Something went wrong: {error_str}', 'code': 500})}\n\n"

            # Always send done so frontend cleans up loading state
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )