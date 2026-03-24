from fastapi import APIRouter, HTTPException
from sqlalchemy import select, delete

from db.models import UserFact, Summary, Session as DBSession
from models.schemas import FactResponse, SummaryResponse, DeleteResponse

router = APIRouter(prefix="/api/memory", tags=["memory"])


# - GET /api/memory/facts/{user_id} 
@router.get("/facts/{user_id}", response_model=list[FactResponse])
async def get_facts(user_id: str):
    """
    Returns all extracted facts about a user.
    Powers the "what I know about you" panel in the frontend.
    Facts are ordered oldest first so the user can see
    what was learned over time.
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        result = await db.execute(
            select(UserFact)
            .where(UserFact.user_id == user_id)
            .order_by(UserFact.created_at.asc())
        )
        facts = result.scalars().all()

        if not facts:
            return []

        return [
            FactResponse(
                id         = f.id,
                user_id    = f.user_id,
                fact       = f.fact,
                created_at = f.created_at,
            )
            for f in facts
        ]

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    finally:
        await db.close()

# - GET /api/memory/summaries/{user_id} 
@router.get("/summaries/{user_id}", response_model=list[SummaryResponse])
async def get_summaries(user_id: str):
    """
    Returns all session summaries for a user across all sessions.
    Powers the memory overview UI in the frontend.
    Ordered newest first - most recent conversations at the top.
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        result = await db.execute(
            select(Summary)
            .join(DBSession, Summary.session_id == DBSession.id)
            .where(DBSession.user_id == user_id)
            .order_by(Summary.created_at.desc())
        )
        summaries = result.scalars().all()

        if not summaries:
            return []

        return [
            SummaryResponse(
                id         = s.id,
                session_id = s.session_id,
                content    = s.content,
                created_at = s.created_at,
            )
            for s in summaries
        ]

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    finally:
        await db.close()


# DELETE /api/memory/facts/{fact_id} 
@router.delete("/facts/{fact_id}", response_model=DeleteResponse)
async def delete_fact(fact_id: str):
    """
    Deletes a specific fact the bot extracted incorrectly.
    The frontend shows a delete button next to each fact
    in the "what I know about you" panel.
    Returns success=True if deleted, success=False if not found.
    """
    from main import db_session_factory

    db = db_session_factory()
    try:
        fact = await db.get(UserFact, fact_id)

        if not fact:
            return DeleteResponse(
                success=False,
                message=f"Fact with id '{fact_id}' not found."
            )

        await db.execute(
            delete(UserFact).where(UserFact.id == fact_id)
        )
        await db.commit()

        return DeleteResponse(
            success=True,
            message="Fact deleted successfully."
        )

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    finally:
        await db.close()