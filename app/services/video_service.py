
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.video_call import VideoCall
from ..schemas.order import VideoCallCreate, VideoCallUpdate
from ..utils.notification_service import send_push_notification   # uses FCM

ROOM_PREFIX = "vendorgpt-room-"

def create_video_call(
    payload: VideoCallCreate,
    vendor_id: int,
    supplier_id: int,
    db: Session
) -> VideoCall:
    room_id = ROOM_PREFIX + str(uuid.uuid4())
    video_call = VideoCall(
        order_id=payload.order_id,
        vendor_id=vendor_id,
        supplier_id=supplier_id,
        room_id=room_id,
        scheduled_time=payload.scheduled_time,
        status="requested"
    )
    db.add(video_call)
    db.commit()
    db.refresh(video_call)

    # notify supplier
    send_push_notification(
        target_uid=supplier_id,
        title="New video verification request",
        body="Vendor requested a product verification call.",
        data={"room_id": room_id, "video_call_id": video_call.id}
    )
    return video_call


def update_video_call(
    call_id: int,
    payload: VideoCallUpdate,
    db: Session
) -> VideoCall:
    video_call = db.query(VideoCall).filter(VideoCall.id == call_id).first()
    if not video_call:
        raise ValueError("Video call not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(video_call, key, value)
    if payload.status == "completed":
        video_call.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(video_call)
    return video_call
