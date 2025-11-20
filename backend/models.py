"""SQLAlchemy models for the application."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from backend.database import Base


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Create case-insensitive unique index on SKU
    __table_args__ = (
        Index('idx_sku_lower', func.lower(sku), unique=True),
    )
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Webhook(Base):
    """Webhook model."""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    event_type = Column(String(50), nullable=False)  # e.g., "upload_complete", "product_created"
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "event_type": self.event_type,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UploadTask(Base):
    """Upload task tracking model."""
    __tablename__ = "upload_tasks"
    
    id = Column(String(100), primary_key=True)  # Celery task ID
    filename = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # Percentage 0-100
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
