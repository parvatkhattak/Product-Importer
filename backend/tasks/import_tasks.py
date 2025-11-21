"""Celery tasks for CSV import processing."""
import csv
import os
from typing import List, Dict
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models import Product, UploadTask
from backend.tasks.webhook_tasks import trigger_webhooks


@celery_app.task(bind=True, name="import_csv")
def import_csv_task(self, task_id: str, file_path: str, filename: str):
    """
    Import CSV file in chunks.
    
    Args:
        task_id: Unique task identifier
        file_path: Path to uploaded CSV file
        filename: Original filename
    """
    db = SessionLocal()
    
    try:
        # Update task status to processing
        upload_task = db.query(UploadTask).filter(UploadTask.id == task_id).first()
        if not upload_task:
            upload_task = UploadTask(
                id=task_id,
                filename=filename,
                status="processing",
                progress=0
            )
            db.add(upload_task)
            db.commit()
        else:
            upload_task.status = "processing"
            db.commit()
        
        # Count total rows first
        with open(file_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for _ in csv.DictReader(f))
        
        upload_task.total_rows = total_rows
        db.commit()
        
        # Process CSV in chunks
        chunk_size = 10000
        processed = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            chunk = []
            
            for row in reader:
                chunk.append(row)
                
                if len(chunk) >= chunk_size:
                    _process_chunk(db, chunk)
                    processed += len(chunk)
                    
                    # Update progress
                    progress = int((processed / total_rows) * 100)
                    upload_task.progress = progress
                    upload_task.processed_rows = processed
                    db.commit()
                    
                    chunk = []
            
            # Process remaining rows
            if chunk:
                _process_chunk(db, chunk)
                processed += len(chunk)
                upload_task.processed_rows = processed
                upload_task.progress = 100
                db.commit()
        
        # Mark as completed
        upload_task.status = "completed"
        db.commit()
        
        # Trigger webhooks
        trigger_webhooks.delay("upload_complete", {
            "task_id": task_id,
            "filename": filename,
            "total_rows": total_rows,
            "status": "completed"
        })
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "completed",
            "total_rows": total_rows,
            "processed_rows": processed
        }
        
    except Exception as e:
        # Update task with error
        upload_task = db.query(UploadTask).filter(UploadTask.id == task_id).first()
        if upload_task:
            upload_task.status = "failed"
            upload_task.error_message = str(e)
            db.commit()
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise e
    
    finally:
        db.close()


def _process_chunk(db, chunk: List[Dict]):
    """
    Process a chunk of CSV rows using bulk upsert.
    
    Args:
        db: Database session
        chunk: List of row dictionaries
    """
    products_data = []
    
    for row in chunk:
        try:
            # Validate and prepare data
            product_data = {
                "sku": row.get("sku", "").strip(),
                "name": row.get("name", "").strip(),
                "description": row.get("description", "").strip() or None,
                "price": float(row.get("price", 0)),
                "active": True  # Default to active
            }
            
            if not product_data["sku"] or not product_data["name"]:
                continue  # Skip invalid rows
            
            products_data.append(product_data)
            
        except (ValueError, KeyError) as e:
            # Skip invalid rows
            continue
    
    if not products_data:
        return

    # Deduplicate within the chunk (keep last occurrence)
    # This prevents "ON CONFLICT DO UPDATE command cannot affect row a second time"
    unique_products = {}
    for p in products_data:
        sku_key = p["sku"].lower()
        unique_products[sku_key] = p
    
    products_data = list(unique_products.values())
    
    # Bulk upsert using PostgreSQL's ON CONFLICT
    # This handles duplicate SKUs (case-insensitive)
    stmt = insert(Product).values(products_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[func.lower(Product.sku)],
        set_={
            "name": stmt.excluded.name,
            "description": stmt.excluded.description,
            "price": stmt.excluded.price,
            "active": stmt.excluded.active,
        }
    )
    
    db.execute(stmt)
    db.commit()
