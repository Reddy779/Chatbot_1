import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db, ChatMessage
from models.schemas import ChatRequest, ChatResponse
from services.groq_client import get_response, MODEL

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):

    # 1. Save the user's message to DB
    db.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        role="user",
        content=request.message,
    ))
    db.commit()

    # 2. Load this session's full history from DB
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .order_by(ChatMessage.timestamp.asc())
        .limit(20)           
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in rows]

    # 3. Call Groq and get the reply
    try:
        reply = get_response(history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")

    # 4. Save the assistant's reply to DB
    db.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        role="assistant",
        content=reply,
    ))
    db.commit()

    # 5. Return plain JSON
    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        model=MODEL,
    )