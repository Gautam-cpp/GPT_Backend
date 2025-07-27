from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class VideoCall(Base):
    __tablename__ = "video_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(String, default="requested")  # requested, accepted, declined, in_progress, completed, cancelled
    scheduled_time = Column(DateTime)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    call_duration = Column(Integer, default=0)  # in seconds
    room_id = Column(String, unique=True)
    quality_assessment = Column(Text)  # JSON string of quality checks
    vendor_satisfaction = Column(Integer)  # 1-5 rating
    supplier_notes = Column(Text)
    recording_url = Column(String)  # Optional recording
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="video_calls")
    vendor = relationship("Vendor", back_populates="video_calls")
    supplier = relationship("Supplier", back_populates="video_calls")
