"""
Tests for Module 05: Authentication & Authorization Practical
"""

import base64
import json
import time
from fastapi.testclient import TestClient
from src.practicals.module_05_auth_demo import (
    app,
    generate_jwt,
    verify_and_decode_jwt
)


def test_module_05_api_key_auth():
    client = TestClient(app)

    # Missing API key (401)
    res_no_key = client.get("/api/service/data")
    assert res_no_key.status_code == 401

    # Invalid API key (401)
    res_bad_key = client.get("/api/service/data", headers={"X-API-Key": "invalid_api_key_99"})
    assert res_bad_key.status_code == 401

    # Valid API key (200)
    res_ok = client.get("/api/service/data", headers={"X-API-Key": "secret-backend-key-12345"})
    assert res_ok.status_code == 200
    assert res_ok.json()["client"] == "payment_worker"


def test_module_05_jwt_login_and_tampering():
    client = TestClient(app)

    # Login customer
    res_login = client.post("/api/auth/login?email=customer@example.com&password=CustomerPassword123!")
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]

    # Access /me
    res_me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["profile"]["email"] == "customer@example.com"
    assert res_me.json()["profile"]["role"] == "customer"

    # Tampering test: Modify role to "admin" without updating HMAC signature
    header_b64, payload_b64, sig_b64 = token.split(".")
    tampered_payload = {"sub": "customer@example.com", "user_id": 2, "role": "admin", "exp": int(time.time()) + 900}
    tampered_b64 = base64.urlsafe_b64encode(json.dumps(tampered_payload, sort_keys=True).encode()).decode().rstrip("=")
    tampered_token = f"{header_b64}.{tampered_b64}.{sig_b64}"

    res_tampered = client.get("/api/users/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_tampered.status_code == 401


def test_module_05_rbac_enforcement():
    client = TestClient(app)

    # Customer token cannot delete item (403 Forbidden)
    res_login_cust = client.post("/api/auth/login?email=customer@example.com&password=CustomerPassword123!")
    cust_token = res_login_cust.json()["access_token"]
    res_del_cust = client.delete("/api/items/10", headers={"Authorization": f"Bearer {cust_token}"})
    assert res_del_cust.status_code == 403

    # Admin token can delete item (200 OK)
    res_login_admin = client.post("/api/auth/login?email=admin@example.com&password=AdminPassword123!")
    admin_token = res_login_admin.json()["access_token"]
    res_del_admin = client.delete("/api/items/10", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_del_admin.status_code == 200
