"""
ActOS — User Model (no Clerk dependency)
Stores bcrypt password hash directly in PostgreSQL
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email              = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password    = Column(String(255), nullable=False)
    first_name         = Column(String(100))
    last_name          = Column(String(100))
    preferred_language = Column(String(50), default="en")
    voice_profile_id   = Column(String(255))
    settings           = Column(JSON, default={})
    is_active          = Column(Boolean, default=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), onupdate=func.now())
