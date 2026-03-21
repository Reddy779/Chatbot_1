from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./chatbot.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(String,   primary_key=True)
    session_id = Column(String,   index=True, nullable=False)
    role       = Column(String,   nullable=False)
    content    = Column(Text,     nullable=False)
    timestamp  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    """Creates all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI dependency — opens a DB session per request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()