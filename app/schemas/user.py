from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    business_name: Optional[str] = Field(None, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    language_preference: str = Field(default="english", max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VendorCreate(VendorBase):
    # Don't include firebase_uid here - it comes from JWT token
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    business_name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    language_preference: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VendorResponse(VendorBase):
    id: int
    firebase_uid: str
    trust_score: float
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class SupplierBase(BaseModel):
    name: str
    business_name: Optional[str] = None
    phone: str
    location: Optional[str] = None
    operating_hours: Optional[str] = None
    delivery_areas: Optional[str] = None

class SupplierCreate(SupplierBase):
    firebase_uid: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fssai_license: Optional[str] = None
    business_registration: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fssai_license: Optional[str] = None
    business_registration: Optional[str] = None
    operating_hours: Optional[str] = None
    delivery_areas: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int
    firebase_uid: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fssai_license: Optional[str] = None
    business_registration: Optional[str] = None
    trust_score: float
    verification_status: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
