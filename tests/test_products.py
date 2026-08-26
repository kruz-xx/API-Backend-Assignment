def test_list_products(client):
    """
    Test listing products catalog with default pagination.
    """
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_filter_products_by_category(client):
    """
    Test query parameter category filtering.
    """
    response = client.get("/api/v1/products/?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["category"] == "Electronics" for p in data)


def test_get_product_by_id(client):
    """
    Test retrieving existing product by ID.
    """
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Mechanical Keyboard"


def test_get_product_not_found(client):
    """
    Test retrieving non-existent product returns 404.
    """
    response = client.get("/api/v1/products/9999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_create_product_admin(client, admin_token):
    """
    Test admin successfully creating a new product.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "4K Ultra-Wide Monitor",
        "description": "34-inch curved gaming and productivity monitor.",
        "price": 499.99,
        "stock": 10,
        "category": "Electronics"
    }
    response = client.post("/api/v1/products/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["price"] == payload["price"]


def test_create_product_forbidden_for_customer(client, customer_token):
    """
    Test non-admin customer creating product receives 403 Forbidden.
    """
    headers = {"Authorization": f"Bearer {customer_token}"}
    payload = {
        "name": "Unauthorized Item",
        "price": 10.0,
        "stock": 5,
        "category": "Test"
    }
    response = client.post("/api/v1/products/", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN_OPERATION"
