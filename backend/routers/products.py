"""Product CRUD API endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from pydantic import BaseModel
from backend.database import get_db
from backend.models import Product
from backend.tasks.webhook_tasks import trigger_webhooks

router = APIRouter(prefix="/api/products", tags=["products"])


# Pydantic schemas
class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    active: bool = True


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: float
    active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("", response_model=dict)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sku: Optional[str] = None,
    name: Optional[str] = None,
    active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List products with filtering and pagination.
    """
    query = db.query(Product)
    
    # Apply filters
    if sku:
        query = query.filter(func.lower(Product.sku).contains(sku.lower()))
    
    if name:
        query = query.filter(func.lower(Product.name).contains(name.lower()))
    
    if active is not None:
        query = query.filter(Product.active == active)
    
    if search:
        search_lower = search.lower()
        query = query.filter(
            or_(
                func.lower(Product.sku).contains(search_lower),
                func.lower(Product.name).contains(search_lower),
                func.lower(Product.description).contains(search_lower)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.order_by(Product.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": [p.to_dict() for p in products]
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get a single product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product.
    """
    # Check for duplicate SKU (case-insensitive)
    existing = db.query(Product).filter(
        func.lower(Product.sku) == product_data.sku.lower()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{product_data.sku}' already exists"
        )
    
    # Create product
    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Trigger webhook
    trigger_webhooks.delay("product_created", product.to_dict())
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check for duplicate SKU if updating SKU
    if product_data.sku and product_data.sku.lower() != product.sku.lower():
        existing = db.query(Product).filter(
            func.lower(Product.sku) == product_data.sku.lower()
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Trigger webhook
    trigger_webhooks.delay("product_updated", product.to_dict())
    
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Delete a single product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_dict = product.to_dict()
    db.delete(product)
    db.commit()
    
    # Trigger webhook
    trigger_webhooks.delay("product_deleted", product_dict)
    
    return None


@router.delete("", status_code=200)
def bulk_delete_products(db: Session = Depends(get_db)):
    """
    Delete all products (bulk delete).
    """
    count = db.query(Product).count()
    db.query(Product).delete()
    db.commit()
    
    # Trigger webhook
    trigger_webhooks.delay("products_bulk_deleted", {"count": count})
    
    return {"deleted": count, "message": f"Successfully deleted {count} products"}
