import uuid
import ast
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import Message, Summary, UserFact, User, Session as DBSession

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# READ OPERATIONS — used by memory_retrieval_node

async def get_recent_messages(
    db: AsyncSession,
    session_id: str,
    limit: int = 20
) -> list[dict]:
    """ 
    Fetches the last `limit` messages for this session from the DB.
    Returns a list of dicts: [{"role": "user", "content": "..."}]

    Why: The LLM needs conversation history to understand context.
    We cap at 20 to keep the context window manageable.
    """

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {"role": m.role, "content": m.content}
        for m in reversed(messages)
    ]


async def get_recent_summaries(
    db: AsyncSession,
    user_id: str,
    limit: int = 3
) -> list[str]:
    """
    Fetches the last `limit` summaries across ALL sessions for this user.
    Returns a list of summary strings.

    Why: Summaries give the LLM context from past sessions without
    sending thousands of raw messages. 3 summaries = enough context
    without overloading the prompt.
    """
    result = await db.execute(
        select(Summary)
        .join(DBSession, Summary.session_id == DBSession.id)
        .where(DBSession.user_id == user_id)
        .order_by(Summary.created_at.desc())
        .limit(limit)
    )
    summaries = result.scalars().all()
    return [s.content for s in summaries]


async def get_user_facts(
    db: AsyncSession,
    user_id: str
) -> list[str]:
    """
    Fetches ALL known facts about this user.
    Returns a list of fact strings.

    Why: Facts like name, location, preferences are injected into
    every system prompt so the LLM always knows who it's talking to.
    """
    result = await db.execute(
        select(UserFact)
        .where(UserFact.user_id == user_id)
        .order_by(UserFact.created_at.asc())
    )
    facts = result.scalars().all()
    return [f.fact for f in facts]


async def get_message_count(
    db: AsyncSession,
    session_id: str
) -> int:
    """
    Returns total number of messages in this session.
    Used by memory_writer_node to decide if summarization is needed.
    """
    result = await db.execute(
        select(func.count())
        .where(Message.session_id == session_id)
    )
    return result.scalar() or 0


# WRITE OPERATIONS — used by memory_writer_node

async def ensure_user_and_session(
    db: AsyncSession,
    user_id: str,
    session_id: str
):
    """
    Creates the user and session rows if they don't exist yet.
    This is idempotent — safe to call on every request.

    Why: The messages table has a foreign key to sessions, and sessions
    has a foreign key to users. So we must ensure both exist before
    saving any message, or we get a foreign key constraint error.
    """
    # Check/create user
    user = await db.get(User, user_id)
    if not user:
        db.add(User(id=user_id, created_at=utcnow()))
        await db.commit()

    # Check/create session
    session = await db.get(DBSession, session_id)
    if not session:
        db.add(DBSession(
            id=session_id,
            user_id=user_id,
            created_at=utcnow()
        ))
        await db.commit()


async def save_message_pair(
    db: AsyncSession,
    session_id: str,
    user_message: str,
    assistant_reply: str
):
    """
    Saves both the user message and assistant reply to the messages table.
    Always saves as a pair so history is always complete.

    Why: We save after the LLM responds (not before) so we never
    save a user message without its corresponding assistant reply.
    """
    db.add(Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=user_message,
        created_at=utcnow(),
    ))
    db.add(Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=assistant_reply,
        created_at=utcnow(),
    ))
    await db.commit()


async def save_user_facts(
    db: AsyncSession,
    user_id: str,
    new_facts: list[str],
    existing_facts: list[str]
):
    """
    Saves newly extracted facts to user_facts table.
    Deduplicates against existing facts before saving.

    Why: We don't want duplicate facts like "name is Dhanush" saved
    10 times. We check if the fact already exists before inserting.
    """
    existing_lower = [f.lower() for f in existing_facts]
    for fact in new_facts:
        if fact.lower() not in existing_lower:
            db.add(UserFact(
                id=str(uuid.uuid4()),
                user_id=user_id,
                fact=fact,
                created_at=utcnow(),
            ))
    await db.commit()

async def save_summary(
    db: AsyncSession,
    session_id: str,
    content: str
):
    """
    Saves a generated summary to the summaries table.
    """
    db.add(Summary(
        id=str(uuid.uuid4()),
        session_id=session_id,
        content=content,
        created_at=utcnow(),
    ))
    await db.commit()


def parse_facts_from_llm(raw_response: str) -> list[str]:
    """
    Parses the LLM's fact extraction response into a Python list.

    The LLM returns something like:
    '["name is Dhanush", "prefers dark mode", "lives in Bangalore"]'

    We use ast.literal_eval which safely parses Python literals
    without using eval() — safer than eval() for untrusted input.
    """
    try:
        cleaned = raw_response.strip()
        facts = ast.literal_eval(cleaned)
        if isinstance(facts, list):
            return [str(f) for f in facts if f]
        return []
    except Exception:
        return []