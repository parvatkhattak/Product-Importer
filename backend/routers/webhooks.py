"""Webhook management API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from backend.database import get_db
from backend.models import Webhook
from backend.tasks.webhook_tasks import test_webhook_task

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# Pydantic schemas
class WebhookCreate(BaseModel):
    url: str
    event_type: str
    enabled: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    event_type: Optional[str] = None
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    event_type: str
    enabled: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    """
    List all webhooks.
    """
    webhooks = db.query(Webhook).order_by(Webhook.id.desc()).all()
    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """
    Get a single webhook by ID.
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return webhook


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(webhook_data: WebhookCreate, db: Session = Depends(get_db)):
    """
    Create a new webhook.
    """
    webhook = Webhook(**webhook_data.dict())
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing webhook.
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Update fields
    update_data = webhook_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(webhook, field, value)
    
    db.commit()
    db.refresh(webhook)
    
    return webhook


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """
    Delete a webhook.
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    
    return None


@router.post("/{webhook_id}/test")
def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """
    Test a webhook by sending a sample payload.
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Run test synchronously to get immediate result
    result = test_webhook_task.apply(args=[webhook.url]).get(timeout=15)
    
    return result
