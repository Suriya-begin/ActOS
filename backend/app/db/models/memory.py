from sqlalchemy import Column, String, Text, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Memory(Base):
    __tablename__ = "memories"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(String(255), nullable=False, index=True)
    category      = Column(String(100), index=True)
    key           = Column(String(255), index=True)
    value         = Column(JSON)
    embedding_id  = Column(String(255))
    confidence    = Column(Float, default=1.0)
    access_count  = Column(String(50), default="0")
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

class Contact(Base):
    __tablename__ = "contacts"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(String(255), nullable=False, index=True)
    name          = Column(String(255), nullable=False)
    alias         = Column(String(255))
    phone         = Column(String(50))
    whatsapp      = Column(String(50))
    email         = Column(String(255))
    preferred_app = Column(String(100), default="whatsapp")
    language      = Column(String(50), default="tamil")
    notes         = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
