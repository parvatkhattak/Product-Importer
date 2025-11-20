"""CSV upload API endpoints."""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models import UploadTask
from backend.tasks.import_tasks import import_csv_task
import asyncio
import json

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UploadResponse(BaseModel):
    task_id: str
    filename: str
    message: str


@router.post("", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file and start import task.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}.csv")
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create upload task record
    upload_task = UploadTask(
        id=task_id,
        filename=file.filename,
        status="pending",
        progress=0
    )
    db.add(upload_task)
    db.commit()
    
    # Start Celery task
    import_csv_task.delay(task_id, file_path, file.filename)
    
    return {
        "task_id": task_id,
        "filename": file.filename,
        "message": "Upload started. Use task_id to track progress."
    }


@router.get("/{task_id}/status")
def get_upload_status(task_id: str, db: Session = Depends(get_db)):
    """
    Get upload task status.
    """
    task = db.query(UploadTask).filter(UploadTask.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.get("/{task_id}/progress")
async def stream_upload_progress(task_id: str, db: Session = Depends(get_db)):
    """
    Server-Sent Events endpoint for real-time progress updates.
    """
    async def event_generator():
        """Generate SSE events with upload progress."""
        while True:
            # Get latest task status
            task = db.query(UploadTask).filter(UploadTask.id == task_id).first()
            
            if not task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break
            
            # Send progress update
            data = {
                "status": task.status,
                "progress": task.progress,
                "processed_rows": task.processed_rows,
                "total_rows": task.total_rows,
                "error_message": task.error_message
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            # Stop streaming if task is completed or failed
            if task.status in ["completed", "failed"]:
                break
            
            # Wait before next update
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
