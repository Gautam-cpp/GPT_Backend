from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..schemas.user import SupplierCreate, SupplierUpdate, SupplierResponse
from ..schemas.product import ProductResponse
from ..models.user import Supplier
from ..models.product import Product
from ..config.database import get_db
from ..utils.auth_utils import get_current_user_firebase_uid, get_current_supplier

router = APIRouter()

@router.post("/", response_model=SupplierResponse)
def create_supplier(
    payload: SupplierCreate, 
    db: Session = Depends(get_db),
    firebase_uid: str = Depends(get_current_user_firebase_uid)
):
    print(f"Creating supplier for Firebase UID: {firebase_uid}")
    
    existing_supplier = db.query(Supplier).filter(Supplier.firebase_uid == firebase_uid).first()
    if existing_supplier:
        raise HTTPException(409, "Supplier already exists")

    try:
        supplier_data = payload.dict()
        supplier_data['firebase_uid'] = firebase_uid
        
        supplier = Supplier(**supplier_data)
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        print(f"Supplier created successfully: {supplier.id}")
        return supplier
        
    except Exception as e:
        db.rollback()
        print(f"Error creating supplier: {e}")
        raise HTTPException(500, f"Failed to create supplier: {str(e)}")

@router.get("/me", response_model=SupplierResponse)
def get_supplier_profile(current: Supplier = Depends(get_current_supplier)):
    return current

@router.patch("/me", response_model=SupplierResponse)
def update_supplier_profile(
    payload: SupplierUpdate,
    current: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db),
):
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current

@router.get("/me/products", response_model=List[ProductResponse])
def get_my_products(
    current: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(Product.supplier_id == current.id).all()
    return products

@router.get("/me/orders")
def get_my_orders(
    current: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    orders = current.orders.all()
    return orders
