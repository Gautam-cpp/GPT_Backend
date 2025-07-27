from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os

from ..config.database import get_db
from ..config.settings import settings
from ..models.user import Vendor, Supplier

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred)

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token"""
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )

def get_current_user_firebase_uid(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract Firebase UID from token"""
    print(f"Received token: {credentials.credentials[:50]}...")
    
    try:
        # Try to decode as Firebase token first
        decoded_token = verify_firebase_token(credentials.credentials)
        print(f"Firebase token decoded successfully: {decoded_token.get('uid')}")
        return decoded_token["uid"]
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        # If Firebase token fails, try JWT token
        try:
            payload = jwt.decode(
                credentials.credentials, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            firebase_uid: str = payload.get("sub")
            print(f"JWT token decoded successfully: {firebase_uid}")
            
            if firebase_uid is None:
                print("No 'sub' field in JWT payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return firebase_uid
        except jwt.JWTError as jwt_error:  # Fixed: Changed from jwt.PyJWTError
            print(f"JWT token verification failed: {jwt_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

def get_current_vendor(
    db: Session = Depends(get_db),
    firebase_uid: str = Depends(get_current_user_firebase_uid)
) -> Vendor:
    """Get current vendor from database"""
    vendor = db.query(Vendor).filter(Vendor.firebase_uid == firebase_uid).first()
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    return vendor

def get_current_supplier(
    db: Session = Depends(get_db),
    firebase_uid: str = Depends(get_current_user_firebase_uid)
) -> Supplier:
    """Get current supplier from database"""
    supplier = db.query(Supplier).filter(Supplier.firebase_uid == firebase_uid).first()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    return supplier

def get_current_user_type(
    db: Session = Depends(get_db),
    firebase_uid: str = Depends(get_current_user_firebase_uid)
) -> dict:
    """Get current user type (vendor or supplier)"""
    vendor = db.query(Vendor).filter(Vendor.firebase_uid == firebase_uid).first()
    if vendor:
        return {"type": "vendor", "user": vendor}
    
    supplier = db.query(Supplier).filter(Supplier.firebase_uid == firebase_uid).first()
    if supplier:
        return {"type": "supplier", "user": supplier}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
