from unittest.mock import patch

def test_upload_csv_valid(client):
    # Mock Celery task
    with patch("backend.tasks.import_tasks.import_csv_task.delay") as mock_task:
        csv_content = "sku,name,price\nP1,Test,10.0"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        assert "task_id" in response.json()
        mock_task.assert_called_once()

def test_upload_invalid_extension(client):
    files = {"file": ("test.txt", "content", "text/plain")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "Only CSV files" in response.json()["detail"]

def test_webhook_crud(client):
    # Create
    res = client.post(
        "/api/webhooks",
        json={"url": "http://example.com", "event_type": "upload_complete"}
    )
    assert res.status_code == 201
    webhook_id = res.json()["id"]
    
    # List
    res = client.get("/api/webhooks")
    assert len(res.json()) == 1
    
    # Delete
    res = client.delete(f"/api/webhooks/{webhook_id}")
    assert res.status_code == 204
    
    # Verify empty
    res = client.get("/api/webhooks")
    assert len(res.json()) == 0
