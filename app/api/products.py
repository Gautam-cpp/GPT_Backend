from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
from ..models.product import Product, ProductImage
from ..models.user import Supplier
from ..config.database import get_db
from ..utils.auth_utils import get_current_supplier

router = APIRouter()

@router.post("/", response_model=ProductResponse)
def create_product(
    payload: ProductCreate,
    current_supplier: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    try:
        product_data = payload.dict()
        product_data['supplier_id'] = current_supplier.id
        
        product = Product(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to create product: {str(e)}")

@router.get("/", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if available_only:
        query = query.filter(Product.is_available == True)
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if min_price:
        query = query.filter(Product.price_per_unit >= min_price)
    if max_price:
        query = query.filter(Product.price_per_unit <= max_price)
    
    products = query.all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_supplier: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_supplier.id
    ).first()
    
    if not product:
        raise HTTPException(404, "Product not found or not owned by you")
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.post("/{product_id}/images")
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    current_supplier: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_supplier.id
    ).first()
    
    if not product:
        raise HTTPException(404, "Product not found")
    
    # Here you would implement actual file upload logic
    # For now, we'll just create a placeholder
    try:
        # Save the uploaded file and get URL
        image_url = f"/images/products/{product_id}/{image.filename}"
        
        product_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            image_type="secondary"
        )
        
        db.add(product_image)
        db.commit()
        db.refresh(product_image)
        
        return {"message": "Image uploaded successfully", "image_url": image_url}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to upload image: {str(e)}")
