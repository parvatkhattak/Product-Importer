"""Celery tasks for webhook processing."""
import httpx
from typing import Dict, Any
from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models import Webhook


@celery_app.task(bind=True, max_retries=3, name="trigger_webhooks")
def trigger_webhooks(self, event_type: str, payload: Dict[str, Any]):
    """
    Trigger all webhooks for a specific event type.
    
    Args:
        event_type: Type of event (e.g., "upload_complete", "product_created")
        payload: Data to send to webhooks
    """
    db = SessionLocal()
    
    try:
        # Get all enabled webhooks for this event type
        webhooks = db.query(Webhook).filter(
            Webhook.event_type == event_type,
            Webhook.enabled == True
        ).all()
        
        for webhook in webhooks:
            try:
                _send_webhook(webhook.url, event_type, payload)
            except Exception as e:
                # Log error but don't fail the task
                print(f"Webhook {webhook.id} failed: {str(e)}")
                continue
        
    finally:
        db.close()


def _send_webhook(url: str, event_type: str, payload: Dict[str, Any]):
    """
    Send HTTP POST request to webhook URL.
    
    Args:
        url: Webhook URL
        event_type: Event type
        payload: Data to send
    """
    data = {
        "event": event_type,
        "data": payload
    }
    
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=data)
        response.raise_for_status()
        
        return {
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }


@celery_app.task(name="test_webhook")
def test_webhook_task(webhook_url: str):
    """
    Test a webhook by sending a sample payload.
    
    Args:
        webhook_url: URL to test
        
    Returns:
        dict: Response status and timing
    """
    try:
        result = _send_webhook(
            webhook_url,
            "test",
            {"message": "This is a test webhook from Product Importer"}
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
