from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class OrderBase(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)
    requirements: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    vendor_rating: Optional[int] = Field(None, ge=1, le=5)
    vendor_feedback: Optional[str] = None
    supplier_notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    id: int
    vendor_id: int
    supplier_id: int
    unit_price: float
    total_amount: float
    status: str
    video_verification_requested: bool
    video_call_completed: bool
    vendor_rating: Optional[int]
    vendor_feedback: Optional[str]
    supplier_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)
