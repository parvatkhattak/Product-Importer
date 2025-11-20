def test_create_product(client):
    response = client.post(
        "/api/products",
        json={
            "sku": "TEST-001",
            "name": "Test Product",
            "description": "A test product",
            "price": 10.50,
            "active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["name"] == "Test Product"

def test_create_duplicate_product_sku(client):
    # Create first product
    client.post(
        "/api/products",
        json={"sku": "TEST-001", "name": "P1", "price": 10.0}
    )
    
    # Try to create duplicate (should fail)
    response = client.post(
        "/api/products",
        json={"sku": "TEST-001", "name": "P2", "price": 20.0}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_create_duplicate_product_sku_case_insensitive(client):
    # Create first product
    client.post(
        "/api/products",
        json={"sku": "TEST-001", "name": "P1", "price": 10.0}
    )
    
    # Try to create duplicate with different case (should fail)
    response = client.post(
        "/api/products",
        json={"sku": "test-001", "name": "P2", "price": 20.0}
    )
    assert response.status_code == 400

def test_read_products(client):
    # Create some products
    client.post("/api/products", json={"sku": "P1", "name": "Prod 1", "price": 10.0})
    client.post("/api/products", json={"sku": "P2", "name": "Prod 2", "price": 20.0})
    
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) == 2
    assert data["total"] == 2

def test_filter_products(client):
    client.post("/api/products", json={"sku": "ABC", "name": "Apple", "price": 10.0})
    client.post("/api/products", json={"sku": "XYZ", "name": "Banana", "price": 20.0})
    
    # Filter by name
    response = client.get("/api/products?name=Apple")
    data = response.json()
    assert len(data["products"]) == 1
    assert data["products"][0]["sku"] == "ABC"

def test_update_product(client):
    # Create product
    res = client.post("/api/products", json={"sku": "P1", "name": "Old Name", "price": 10.0})
    prod_id = res.json()["id"]
    
    # Update
    response = client.put(
        f"/api/products/{prod_id}",
        json={"name": "New Name", "price": 15.0}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["price"] == 15.0

def test_delete_product(client):
    res = client.post("/api/products", json={"sku": "P1", "name": "To Delete", "price": 10.0})
    prod_id = res.json()["id"]
    
    response = client.delete(f"/api/products/{prod_id}")
    assert response.status_code == 204
    
    # Verify deleted
    get_res = client.get(f"/api/products/{prod_id}")
    assert get_res.status_code == 404
