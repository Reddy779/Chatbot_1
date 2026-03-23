from pydantic import BaseModel, Field
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    user_id:    str = Field(..., min_length=1, max_length=64)
    message:    str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: str
    user_id:    str
    reply:      str
    model:      str


class AgentState(BaseModel):
    messages:   Annotated[list[BaseMessage], add_messages]
    user_id:    str
    session_id: str
    user_facts: list[str] = []
    summaries:  list[str] = []

    class Config:
        arbitrary_types_allowed = True