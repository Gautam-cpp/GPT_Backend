from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, preparing, delivered, cancelled
    requirements = Column(Text)  # Original vendor requirements
    delivery_address = Column(Text)
    delivery_date = Column(DateTime)
    video_verification_requested = Column(Boolean, default=False)
    video_call_completed = Column(Boolean, default=False)
    vendor_rating = Column(Integer)  # 1-5 rating from vendor
    vendor_feedback = Column(Text)
    supplier_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    video_calls = relationship("VideoCall", back_populates="order", lazy="dynamic")
    order_items = relationship("OrderItem", back_populates="order", lazy="dynamic")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")
