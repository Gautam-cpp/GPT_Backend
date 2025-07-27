from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VideoCallBase(BaseModel):
    order_id: int
    scheduled_time: Optional[datetime] = None

class VideoCallCreate(VideoCallBase):
    pass

class VideoCallUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    quality_assessment: Optional[str] = None
    vendor_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    supplier_notes: Optional[str] = None
    recording_url: Optional[str] = None

class VideoCallResponse(VideoCallBase):
    id: int
    vendor_id: int
    supplier_id: int
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    call_duration: int
    room_id: str
    quality_assessment: Optional[str]
    vendor_satisfaction: Optional[int]
    supplier_notes: Optional[str]
    recording_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
