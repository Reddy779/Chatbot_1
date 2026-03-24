from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional
from datetime import datetime
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


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    title:   Optional[str] = Field(None, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    user_id:    str
    title:      Optional[str]
    created_at: datetime
    last_active: Optional[datetime]

    class Config:
        from_attributes = True


class FactResponse(BaseModel):
    id:         str
    user_id:    str
    fact:       str
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    id:         str
    session_id: str
    content:    str
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    success: bool
    message: str



class AgentState(BaseModel):
    messages:   Annotated[list[BaseMessage], add_messages]
    user_id:    str
    session_id: str
    user_facts: list[str] = []
    summaries:  list[str] = []
    history: list[dict] = []
    message_count: int = 0

    next_agent: Literal["chat_agent", "research_agent", "tool_agent"] = "chat_agent"

    class Config:
        arbitrary_types_allowed = True