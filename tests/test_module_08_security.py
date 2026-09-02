"""
Tests for Module 08: API Security Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_08_security_demo import app


def test_module_08_negative_quantity_protection():
    client = TestClient(app)

    # Malicious negative quantity payload rejected with 422
    payload = {"customer_id": 10, "items": [{"product_id": 1, "quantity": -5, "unit_price": 40.00}]}
    res = client.post("/api/v1/orders/checkout", json=payload)
    assert res.status_code == 422


def test_module_08_cors_preflight():
    client = TestClient(app)

    # Preflight OPTIONS request from whitelisted origin
    res = client.options(
        "/api/v1/orders/checkout",
        headers={
            "Origin": "https://trusted-dashboard.example.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://trusted-dashboard.example.com"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_module_08_scoped_tokens():
    client = TestClient(app)

    # Analytics token cannot charge order (403 Forbidden)
    res_forbidden = client.post("/api/v1/orders/charge?order_id=1", headers={"Authorization": "Bearer token_analytics_123"})
    assert res_forbidden.status_code == 403

    # Payment token can charge order (200 OK)
    res_ok = client.post("/api/v1/orders/charge?order_id=1", headers={"Authorization": "Bearer token_payment_456"})
    assert res_ok.status_code == 200


def test_module_08_bola_idor_protection():
    client = TestClient(app)

    # User 101 accessing User 101's invoice (200 OK)
    res_ok = client.get("/api/v1/invoices/1", headers={"X-User-ID": "101"})
    assert res_ok.status_code == 200

    # User 101 attempting to access User 102's private invoice (403 Forbidden)
    res_forbidden = client.get("/api/v1/invoices/2", headers={"X-User-ID": "101"})
    assert res_forbidden.status_code == 403
