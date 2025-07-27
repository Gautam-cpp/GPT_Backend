from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
from ..models.order import Order, OrderItem
from ..models.user import Vendor, Supplier
from ..models.product import Product
from ..config.database import get_db
from ..utils.auth_utils import get_current_vendor, get_current_supplier, get_current_user_type

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order(
    payload: OrderCreate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    try:
        # Verify product exists and is available
        product = db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise HTTPException(404, "Product not found")
        
        if not product.is_available:
            raise HTTPException(400, "Product is not available")
        
        if product.available_quantity < payload.quantity:
            raise HTTPException(400, "Insufficient product quantity")
        
        # Calculate total amount
        total_amount = product.price_per_unit * payload.quantity
        
        # Create order
        order_data = payload.dict()
        order_data.update({
            'vendor_id': current_vendor.id,
            'supplier_id': product.supplier_id,
            'unit_price': product.price_per_unit,
            'total_amount': total_amount,
            'status': 'pending'
        })
        
        order = Order(**order_data)
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Update product quantity
        product.available_quantity -= payload.quantity
        db.commit()
        
        return order
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to create order: {str(e)}")

@router.get("/", response_model=List[OrderResponse])
def get_orders(
    status: Optional[str] = None,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user_type = current_user["type"]
    user = current_user["user"]
    
    query = db.query(Order)
    
    if user_type == "vendor":
        query = query.filter(Order.vendor_id == user.id)
    elif user_type == "supplier":
        query = query.filter(Order.supplier_id == user.id)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    query = db.query(Order).filter(Order.id == order_id)
    
    if user_type == "vendor":
        query = query.filter(Order.vendor_id == user.id)
    elif user_type == "supplier":
        query = query.filter(Order.supplier_id == user.id)
    
    order = query.first()
    if not order:
        raise HTTPException(404, "Order not found")
    
    return order

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderUpdate,
    current_user = Depends(get_current_user_type),
    db: Session = Depends(get_db)
):
    user = current_user["user"]
    user_type = current_user["type"]
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    
    # Verify user can update this order
    if user_type == "vendor" and order.vendor_id != user.id:
        raise HTTPException(403, "Not authorized to update this order")
    elif user_type == "supplier" and order.supplier_id != user.id:
        raise HTTPException(403, "Not authorized to update this order")
    
    try:
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
        
        return {"message": "Order updated successfully", "order": order}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to update order: {str(e)}")
