from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.database import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id         = Column(String,   primary_key=True)
    name       = Column(String,   nullable=True)
    created_at = Column(DateTime, default=utcnow)

    sessions   = relationship("Session",  back_populates="user")
    facts      = relationship("UserFact", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id         = Column(String,   primary_key=True)  # = LangGraph thread_id
    user_id    = Column(String,   ForeignKey("users.id"), nullable=False, index=True)
    title       = Column(String,   nullable=True)           
    last_active = Column(DateTime, nullable=True) 
    created_at = Column(DateTime, default=utcnow)

    user       = relationship("User",    back_populates="sessions")
    messages   = relationship("Message", back_populates="session")
    summaries  = relationship("Summary", back_populates="session")


class Message(Base):
    __tablename__ = "messages"

    id         = Column(String,   primary_key=True)
    session_id = Column(String,   ForeignKey("sessions.id"), nullable=False, index=True)
    role       = Column(String,   nullable=False)   # "user" or "assistant"
    content    = Column(Text,     nullable=False)
    created_at = Column(DateTime, default=utcnow)

    session    = relationship("Session", back_populates="messages")


class Summary(Base):
    __tablename__ = "summaries"

    id         = Column(String,   primary_key=True)
    session_id = Column(String,   ForeignKey("sessions.id"), nullable=False, index=True)
    content    = Column(Text,     nullable=False)
    created_at = Column(DateTime, default=utcnow)

    session    = relationship("Session", back_populates="summaries")


class UserFact(Base):
    __tablename__ = "user_facts"

    id         = Column(String,   primary_key=True)
    user_id    = Column(String,   ForeignKey("users.id"), nullable=False, index=True)
    fact       = Column(Text,     nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user       = relationship("User", back_populates="facts")