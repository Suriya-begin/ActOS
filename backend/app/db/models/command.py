from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Command(Base):
    __tablename__ = "commands"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(String(255), nullable=False, index=True)
    raw_text      = Column(Text, nullable=False)
    language      = Column(String(50))
    intent        = Column(String(100))
    app_target    = Column(String(100))
    params        = Column(JSON, default={})
    agent_used    = Column(String(100))
    status        = Column(String(50), default="pending")
    result        = Column(JSON, default={})
    error         = Column(Text, nullable=True)
    auth_required = Column(Boolean, default=False)
    auth_passed   = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    completed_at  = Column(DateTime(timezone=True), nullable=True)
