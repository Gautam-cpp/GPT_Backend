from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    price_per_unit = Column(Float, nullable=False)
    unit_type = Column(String, default="kg")  # kg, piece, liter, etc.
    minimum_order_quantity = Column(Float, default=1.0)
    available_quantity = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    description = Column(Text)
    image_urls = Column(Text)  # JSON string of image URLs
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    orders = relationship("Order", back_populates="product", lazy="dynamic")
    product_images = relationship("ProductImage", back_populates="product", lazy="dynamic")

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String, nullable=False)
    image_type = Column(String, default="primary")  # primary, secondary, quality_check
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    product = relationship("Product", back_populates="product_images")
