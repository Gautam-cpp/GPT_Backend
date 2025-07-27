from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import uuid
from ..schemas.video_call import VideoCallCreate, VideoCallUpdate, VideoCallResponse
from ..models.video_call import VideoCall
from ..models.order import Order
from ..models.user import Vendor, Supplier
from ..config.database import get_db
from ..utils.auth_utils import get_current_user_type

router = APIRouter()

@router.post("/", response_model=VideoCallResponse)
def request_video_call(
    payload: VideoCallCreate,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    # Verify order exists and user has access
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    
    if user_type == "vendor" and order.vendor_id != user.id:
        raise HTTPException(403, "Not authorized for this order")
    elif user_type == "supplier" and order.supplier_id != user.id:
        raise HTTPException(403, "Not authorized for this order")
    
    try:
        # Check if video call already exists for this order
        existing_call = db.query(VideoCall).filter(
            VideoCall.order_id == payload.order_id,
            VideoCall.status.in_(["requested", "accepted", "in_progress"])
        ).first()
        
        if existing_call:
            raise HTTPException(400, "Video call already exists for this order")
        
        # Create video call
        video_call_data = payload.dict()
        video_call_data.update({
            'vendor_id': order.vendor_id,
            'supplier_id': order.supplier_id,
            'room_id': str(uuid.uuid4()),
            'status': 'requested'
        })
        
        video_call = VideoCall(**video_call_data)
        db.add(video_call)
        db.commit()
        db.refresh(video_call)
        
        # Update order to indicate video verification requested
        order.video_verification_requested = True
        db.commit()
        
        return video_call
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to create video call: {str(e)}")

@router.get("/", response_model=List[VideoCallResponse])
def get_video_calls(
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    query = db.query(VideoCall)
    
    if user_type == "vendor":
        query = query.filter(VideoCall.vendor_id == user.id)
    elif user_type == "supplier":
        query = query.filter(VideoCall.supplier_id == user.id)
    
    video_calls = query.order_by(VideoCall.created_at.desc()).all()
    return video_calls

@router.get("/{call_id}", response_model=VideoCallResponse)
def get_video_call(
    call_id: int,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    query = db.query(VideoCall).filter(VideoCall.id == call_id)
    
    if user_type == "vendor":
        query = query.filter(VideoCall.vendor_id == user.id)
    elif user_type == "supplier":
        query = query.filter(VideoCall.supplier_id == user.id)
    
    video_call = query.first()
    if not video_call:
        raise HTTPException(404, "Video call not found")
    
    return video_call

@router.patch("/{call_id}", response_model=VideoCallResponse)
def update_video_call(
    call_id: int,
    payload: VideoCallUpdate,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    video_call = db.query(VideoCall).filter(VideoCall.id == call_id).first()
    if not video_call:
        raise HTTPException(404, "Video call not found")
    
    # Verify user can update this call
    if user_type == "vendor" and video_call.vendor_id != user.id:
        raise HTTPException(403, "Not authorized to update this video call")
    elif user_type == "supplier" and video_call.supplier_id != user.id:
        raise HTTPException(403, "Not authorized to update this video call")
    
    try:
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(video_call, key, value)
        
        # Update timestamps based on status
        if payload.status == "in_progress" and not video_call.started_at:
            video_call.started_at = datetime.utcnow()
        elif payload.status == "completed" and not video_call.ended_at:
            video_call.ended_at = datetime.utcnow()
            if video_call.started_at:
                duration = (video_call.ended_at - video_call.started_at).seconds
                video_call.call_duration = duration
            
            # Update order status
            order = db.query(Order).filter(Order.id == video_call.order_id).first()
            if order:
                order.video_call_completed = True
                
        db.commit()
        db.refresh(video_call)
        
        return video_call
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to update video call: {str(e)}")
