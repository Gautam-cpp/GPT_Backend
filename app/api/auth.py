from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..config.database import get_db
from ..utils.auth_utils import verify_firebase_token, create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    id_token: str

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        print(f"Login attempt with ID token: {payload.id_token[:50]}...")
        
        # Verify Firebase token
        decoded_token = verify_firebase_token(payload.id_token)
        firebase_uid = decoded_token["uid"]
        
        print(f"Firebase UID extracted: {firebase_uid}")
        
        # Create JWT with Firebase UID as subject
        access_token = create_access_token(
            data={"sub": firebase_uid}
        )
        
        print(f"JWT token created: {access_token[:50]}...")
        print("Login successful")
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Login failed with error: {e}")
        print(f"Error type: {type(e)}")
        raise HTTPException(401, f"Authentication failed: {str(e)}")
