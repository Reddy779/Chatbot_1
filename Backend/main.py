import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.graph import build_graph

load_dotenv()

def clean_url(url: str) -> str:
    url = url.replace("?sslmode=require", "")
    url = url.replace("&sslmode=require", "")
    url = url.replace("?ssl=require", "")
    url = url.replace("&ssl=require", "")
    return url

engine = create_async_engine(
    clean_url(os.getenv("DATABASE_URL", "")),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"ssl": "require"},
)

db_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

app_state = {}

# def clean_checkpoint_url() -> str:
#     """
#     AsyncPostgresSaver uses asyncpg internally.
#     asyncpg does NOT accept sslmode=require in the URL.
#     We strip all SSL params from the URL — Neon works without
#     them being explicitly set in the connection string.
#     """
#     url = os.getenv("CHECKPOINT_DB_URL", "")
#     url = url.replace("?sslmode=require", "")
#     url = url.replace("&sslmode=require", "")
#     url = url.replace("?ssl=require", "")
#     url = url.replace("&ssl=require", "")
#     return url

@asynccontextmanager
async def lifespan(app: FastAPI):
    checkpoint_url = clean_url(os.getenv("CHECKPOINT_DB_URL", ""))
    print(f"Connecting checkpointer to: {checkpoint_url[:55]}...")

    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_url
    ) as checkpointer:
        await checkpointer.setup()
        app_state["graph"] = build_graph(checkpointer)
        print("Graph ready, connected to Neon DB")
        yield

    await engine.dispose()

app = FastAPI(
    title="DR Chatbot API",
    description="Chatbot with multi-agent LangGraph + long-term memory"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

from routers.chat     import router as chat_router
from routers.sessions import router as sessions_router
from routers.memory   import router as memory_router

app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(memory_router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db":     "neon",
        "agents": ["chat_agent", "research_agent", "tool_agent"]
    }