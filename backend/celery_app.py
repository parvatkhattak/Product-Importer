"""Celery application configuration."""
import os
from celery import Celery
from backend.config import settings

# Validate Redis URL
redis_url = settings.redis_url
print(f"[CELERY] Using Redis URL: {redis_url[:20]}...")  # Print first 20 chars for security

# Ensure Redis URL is valid
if not redis_url or not (redis_url.startswith('redis://') or redis_url.startswith('rediss://')):
    raise ValueError(f"Invalid REDIS_URL: {redis_url[:50]}... - must start with redis:// or rediss://")

# Create Celery application
celery_app = Celery(
    "product_importer",
    broker=redis_url,
    backend=redis_url,
    include=[
        "backend.tasks.import_tasks",
        "backend.tasks.webhook_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    broker_connection_retry_on_startup=True,
)

if __name__ == "__main__":
    celery_app.start()
