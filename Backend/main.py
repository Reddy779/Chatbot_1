from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from services.graph import build_graph
import os
from dotenv import load_dotenv

load_dotenv()

# Global graph reference
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open checkpointer connection and keep it alive for entire app lifetime
    async with AsyncPostgresSaver.from_conn_string(
        os.getenv("CHECKPOINT_DB_URL")
    ) as checkpointer:
        await checkpointer.setup()           # creates LangGraph tables in Neon
        app_state["graph"] = build_graph(checkpointer)
        print("Graph ready, connected to Neon DB")
        yield                                # app runs here
    # checkpointer connection closes cleanly when app shuts down

app = FastAPI(title="DR Chatbot", version="1.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

from routers.chat import router
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok", "phase": "2", "db": "neon"}