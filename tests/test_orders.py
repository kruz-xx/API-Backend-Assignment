def test_create_order_success(client, customer_token):
    """
    Test customer creating an order with valid stock.
    """
    headers = {"Authorization": f"Bearer {customer_token}"}
    payload = {
        "items": [
            {"product_id": 1, "quantity": 2},  # $89.99 * 2 = 179.98
            {"product_id": 2, "quantity": 1}   # $39.99 * 1 = 39.99
        ]
    }
    response = client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == 219.97
    assert len(data["items"]) == 2
    assert data["status"] == "pending"


def test_create_order_insufficient_stock(client, customer_token):
    """
    Test ordering more units than available returns 400 Bad Request.
    """
    headers = {"Authorization": f"Bearer {customer_token}"}
    payload = {
        "items": [
            {"product_id": 1, "quantity": 500}  # Available stock is only 20
        ]
    }
    response = client.post("/api/v1/orders/", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_STOCK"


def test_list_user_orders(client, customer_token):
    """
    Test customer listing their own placed orders.
    """
    headers = {"Authorization": f"Bearer {customer_token}"}
    # Create order first
    payload = {
        "items": [{"product_id": 2, "quantity": 1}]
    }
    client.post("/api/v1/orders/", json=payload, headers=headers)

    response = client.get("/api/v1/orders/", headers=headers)
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) >= 1
    assert orders[0]["user_id"] == 2


def test_order_bola_protection(client, customer_token, admin_token):
    """
    Test Broken Object Level Authorization: Customer A cannot access Customer B's order.
    """
    # Create order as customer (user_id = 2)
    headers_customer = {"Authorization": f"Bearer {customer_token}"}
    payload = {
        "items": [{"product_id": 1, "quantity": 1}]
    }
    order_res = client.post("/api/v1/orders/", json=payload, headers=headers_customer)
    order_id = order_res.json()["id"]

    # Register another customer (user_id = 3)
    reg_payload = {
        "email": "other@example.com",
        "full_name": "Other Person",
        "password": "Password123!",
        "role": "customer"
    }
    client.post("/api/v1/users/register", json=reg_payload)
    login_res = client.post("/api/v1/users/login", json={"email": "other@example.com", "password": "Password123!"})
    other_token = login_res.json()["access_token"]

    # Other customer tries to view order_id of first customer
    response = client.get(f"/api/v1/orders/{order_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN_RESOURCE"
