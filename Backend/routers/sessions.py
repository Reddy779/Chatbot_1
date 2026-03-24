import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Session as DBSession, User
from models.schemas import CreateSessionRequest, SessionResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# - POST /api/sessions
@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest):
    """
    Creates a new session for a user and returns the session_id.
    If the user doesn't exist yet, creates them too.
    The frontend calls this when the user clicks "New Chat".
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        # Ensure user exists
        user = await db.get(User, request.user_id)
        if not user:
            db.add(User(id=request.user_id, created_at=utcnow()))
            await db.commit()

        # Create new session
        session_id = str(uuid.uuid4())
        title      = request.title or f"Chat {datetime.now().strftime('%b %d, %Y %H:%M')}"

        new_session = DBSession(
            id          = session_id,
            user_id     = request.user_id,
            title       = title,
            created_at  = utcnow(),
            last_active = utcnow(),
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        return SessionResponse(
            session_id  = new_session.id,
            user_id     = new_session.user_id,
            title       = new_session.title,
            created_at  = new_session.created_at,
            last_active = new_session.last_active,
        )

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    finally:
        await db.close()


# - GET /api/sessions/{user_id} 
@router.get("/{user_id}", response_model=list[SessionResponse])
async def get_sessions(user_id: str):
    """
    Returns all sessions for a user ordered by last_active descending.
    Powers the session history sidebar in the frontend.
    Each item shows the session title and last active timestamp.
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        result = await db.execute(
            select(DBSession)
            .where(DBSession.user_id == user_id)
            .order_by(DBSession.last_active.desc())
        )
        sessions = result.scalars().all()

        if not sessions:
            return []

        return [
            SessionResponse(
                session_id  = s.id,
                user_id     = s.user_id,
                title       = s.title,
                created_at  = s.created_at,
                last_active = s.last_active,
            )
            for s in sessions
        ]

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    finally:
        await db.close()