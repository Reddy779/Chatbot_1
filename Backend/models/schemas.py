from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    message:    str = Field(..., min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    session_id: str
    reply:      str
    model:      str