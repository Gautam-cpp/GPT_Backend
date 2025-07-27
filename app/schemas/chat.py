from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: Optional[str] = Field(default="english", regex="^(english|hindi)$")

class RequirementExtraction(BaseModel):
    product_name: str
    quantity: float
    unit: str
    budget: Optional[float] = None
    urgency: str = Field(default="normal", regex="^(urgent|normal|flexible)$")
    quality_preference: str = Field(default="good", regex="^(premium|good|basic)$")
    location_preference: Optional[str] = None
    confidence_score: float = Field(..., ge=0, le=1)

class ProductMatch(BaseModel):
    product_id: int
    supplier_id: int
    supplier_name: str
    product_name: str
    price_per_unit: float
    unit_type: str
    available_quantity: float
    quality_score: float
    trust_score: float
    distance_km: float
    image_urls: List[str] = []
    total_cost: float
    phone: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    products: List[Dict[str, Any]] = []
    requires_clarification: bool = False
    extracted_requirements: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    id: int
    message_type: str
    message_content: str
    extracted_requirements: Optional[str]
    suggested_products: Optional[str]
    created_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True
