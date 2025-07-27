from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    business_name = Column(String)
    phone = Column(String, unique=True, index=True)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    business_type = Column(String)
    language_preference = Column(String, default="hindi")
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    orders = relationship("Order", back_populates="vendor", lazy="dynamic")
    video_calls = relationship("VideoCall", back_populates="vendor", lazy="dynamic")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    business_name = Column(String)
    phone = Column(String, unique=True, index=True)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    fssai_license = Column(String)
    business_registration = Column(String)
    trust_score = Column(Float, default=0.0)
    operating_hours = Column(String)
    delivery_areas = Column(Text)
    verification_status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    products = relationship("Product", back_populates="supplier", lazy="dynamic")
    orders = relationship("Order", back_populates="supplier", lazy="dynamic")
    video_calls = relationship("VideoCall", back_populates="supplier", lazy="dynamic")
