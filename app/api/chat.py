from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.chat import ChatRequest, ChatResponse
from ..models.chat import ChatSession, ChatMessage
from ..models.user import Vendor
from ..config.database import get_db
from ..utils.auth_utils import get_current_vendor
from ..services.ai_agent import VendorGPTAgent
import uuid

router = APIRouter()
agent = VendorGPTAgent()

@router.post("/", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    try:
        # Get or create chat session
        session = db.query(ChatSession).filter(
            ChatSession.vendor_id == current_vendor.id,
            ChatSession.status == "active"
        ).first()
        
        if not session:
            session = ChatSession(
                vendor_id=current_vendor.id,
                session_id=str(uuid.uuid4()),
                status="active"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            message_type="user",
            message_content=payload.message,
            is_processed=False
        )
        db.add(user_message)
        db.commit()
        
        # Generate AI response
        ai_response = agent.generate_response(
            message=payload.message,
            vendor_id=current_vendor.id,
            language=payload.language or "english",
            db=db
        )
        
        # Save bot message
        bot_message = ChatMessage(
            session_id=session.id,
            message_type="bot",
            message_content=ai_response.response,
            extracted_requirements=str(ai_response.extracted_requirements),
            suggested_products=str([p for p in ai_response.products]),
            is_processed=True
        )
        db.add(bot_message)
        db.commit()
        
        return ai_response
        
    except Exception as e:
        db.rollback()
        print(f"Chat error: {e}")
        raise HTTPException(500, f"Chat processing failed: {str(e)}")

@router.get("/history")
def get_chat_history(
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.vendor_id == current_vendor.id,
        ChatSession.status == "active"
    ).first()
    
    if not session:
        return {"messages": []}
    
    messages = session.messages.order_by(ChatMessage.created_at).all()
    return {"messages": messages}
