from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    session_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="active")  # active, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime)
    
    # Relationships
    vendor = relationship("Vendor")
    messages = relationship("ChatMessage", back_populates="session", lazy="dynamic")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String, nullable=False)  # user, bot, system
    message_content = Column(Text, nullable=False)
    extracted_requirements = Column(Text)  # JSON string of extracted requirements
    suggested_products = Column(Text)  # JSON string of product suggestions
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
