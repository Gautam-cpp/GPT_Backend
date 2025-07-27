from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.user import VendorCreate, VendorUpdate, VendorResponse
from ..models.user import Vendor
from ..config.database import get_db
from ..utils.auth_utils import get_current_user_firebase_uid, get_current_vendor

router = APIRouter()

@router.post("/", response_model=VendorResponse)
def create_vendor(
    payload: VendorCreate, 
    db: Session = Depends(get_db),
    firebase_uid: str = Depends(get_current_user_firebase_uid)
):
    print(f"Creating vendor for Firebase UID: {firebase_uid}")
    print(f"Payload received: {payload.dict()}")
    
    # Check if vendor already exists
    existing_vendor = db.query(Vendor).filter(Vendor.firebase_uid == firebase_uid).first()
    if existing_vendor:
        print(f"Vendor already exists: {existing_vendor.id}")
        raise HTTPException(409, "Vendor already exists")

    try:
        # Create vendor with firebase_uid from JWT token
        vendor_data = payload.dict()
        vendor_data['firebase_uid'] = firebase_uid
        
        print(f"Creating vendor with data: {vendor_data}")
        
        vendor = Vendor(**vendor_data)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        
        print(f"Vendor created successfully: {vendor.id}")
        return vendor
        
    except Exception as e:
        db.rollback()
        print(f"Error creating vendor: {e}")
        raise HTTPException(500, f"Failed to create vendor: {str(e)}")

# ... rest of your endpoints remain the same


@router.get("/me", response_model=VendorResponse)
def get_vendor_profile(current: Vendor = Depends(get_current_vendor)):
    return current

@router.patch("/me", response_model=VendorResponse)
def update_vendor_profile(
    payload: VendorUpdate,
    current: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current
