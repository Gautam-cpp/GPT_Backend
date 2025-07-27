from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    price_per_unit: float = Field(..., gt=0)
    unit_type: str = Field(default="kg", max_length=20)
    minimum_order_quantity: float = Field(default=1.0, gt=0)
    available_quantity: float = Field(default=0.0, ge=0)
    description: Optional[str] = None
    is_available: bool = Field(default=True)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    price_per_unit: Optional[float] = Field(None, gt=0)
    unit_type: Optional[str] = Field(None, max_length=20)
    minimum_order_quantity: Optional[float] = Field(None, gt=0)
    available_quantity: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_available: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    supplier_id: int
    quality_score: float
    image_urls: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProductImageResponse(BaseModel):
    id: int
    product_id: int
    image_url: str
    image_type: str
    uploaded_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
