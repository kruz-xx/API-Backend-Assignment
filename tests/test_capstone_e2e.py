"""
Module 12 Capstone: Comprehensive End-to-End API Test Suite
Validates the integrated production lifecycle across all modules:
Authentication -> RBAC -> Catalog Management -> Filtering -> Transactions -> BOLA Protection -> GraphQL
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.routers.orders import orders_db
from src.routers.products import products_db
from src.routers.users import users_db


@pytest.fixture(autouse=True)
def clean_database_stores():
    users_db.clear()
    orders_db.clear()
    # Re-seed baseline products
    products_db.clear()
    products_db[1] = {
        "id": 1,
        "name": "Mechanical Keyboard",
        "description": "RGB Backlit keyboard",
        "price": 89.99,
        "stock": 10,
        "category": "Electronics"
    }
    products_db[2] = {
        "id": 2,
        "name": "Wireless Mouse",
        "description": "Ergonomic mouse",
        "price": 49.99,
        "stock": 20,
        "category": "Electronics"
    }
    yield


def test_capstone_full_ecommerce_lifecycle():
    client = TestClient(app)

    # 1. Health Probe
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 2. Register Admin & Customer
    res_reg_admin = client.post(
        "/api/v1/users/register",
        json={"email": "admin@store.com", "password": "AdminPassword123!", "full_name": "Store Admin", "role": "admin"}
    )
    assert res_reg_admin.status_code == 201

    res_reg_cust = client.post(
        "/api/v1/users/register",
        json={"email": "sarah@store.com", "password": "SarahPassword123!", "full_name": "Sarah Connor", "role": "customer"}
    )
    assert res_reg_cust.status_code == 201

    res_reg_cust2 = client.post(
        "/api/v1/users/register",
        json={"email": "john@store.com", "password": "JohnPassword123!", "full_name": "John Connor", "role": "customer"}
    )
    assert res_reg_cust2.status_code == 201

    # 3. Authenticate and retrieve JWT tokens
    admin_token = client.post("/api/v1/users/login", json={"email": "admin@store.com", "password": "AdminPassword123!"}).json()["access_token"]
    sarah_token = client.post("/api/v1/users/login", json={"email": "sarah@store.com", "password": "SarahPassword123!"}).json()["access_token"]
    john_token = client.post("/api/v1/users/login", json={"email": "john@store.com", "password": "JohnPassword123!"}).json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    sarah_headers = {"Authorization": f"Bearer {sarah_token}"}
    john_headers = {"Authorization": f"Bearer {john_token}"}

    # 4. Admin creates new product
    res_new_prod = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={"name": "Studio Headphones", "description": "High fidelity audio", "price": 149.99, "stock": 15, "category": "Audio"}
    )
    assert res_new_prod.status_code == 201
    prod_id = res_new_prod.json()["id"]

    # 5. Customer attempts admin action (Product creation rejected with 403)
    res_unauth_prod = client.post(
        "/api/v1/products/",
        headers=sarah_headers,
        json={"name": "Fake Product", "price": 10.0, "stock": 5, "category": "Audio"}
    )
    assert res_unauth_prod.status_code == 403

    # 6. Customer lists products with category filter
    res_catalog = client.get("/api/v1/products/?category=audio")
    assert res_catalog.status_code == 200
    assert len(res_catalog.json()) == 1
    assert res_catalog.json()[0]["id"] == prod_id

    # 7. Customer places an order (Inventory deduction check)
    initial_stock = products_db[1]["stock"]
    order_payload = {
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": prod_id, "quantity": 1}
        ]
    }
    res_order = client.post("/api/v1/orders/", headers=sarah_headers, json=order_payload)
    assert res_order.status_code == 201
    order_data = res_order.json()
    order_id = order_data["id"]
    assert order_data["total_amount"] == round((89.99 * 2) + 149.99, 2)
    # Check inventory was deducted correctly
    assert products_db[1]["stock"] == initial_stock - 2

    # 8. Insufficient inventory order failure (400 Bad Request)
    res_excessive_order = client.post(
        "/api/v1/orders/",
        headers=sarah_headers,
        json={"items": [{"product_id": 1, "quantity": 9999}]}
    )
    assert res_excessive_order.status_code == 400

    # 9. BOLA Protection: Sarah can read her own order
    res_sarah_order = client.get(f"/api/v1/orders/{order_id}", headers=sarah_headers)
    assert res_sarah_order.status_code == 200
    assert res_sarah_order.json()["id"] == order_id

    # 10. BOLA Protection: John cannot read Sarah's order (403 Forbidden)
    res_john_attack = client.get(f"/api/v1/orders/{order_id}", headers=john_headers)
    assert res_john_attack.status_code == 403
    assert res_john_attack.json()["error"]["code"] == "FORBIDDEN_RESOURCE"

    # 11. Query catalog via GraphQL endpoint
    gql_res = client.post("/graphql", json={"query": "{ products { id name price } }"})
    assert gql_res.status_code == 200
    assert len(gql_res.json()["data"]["products"]) >= 3
