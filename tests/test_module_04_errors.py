"""
Tests for Module 04: Errors, Validation & Response Design Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_04_error_handling import app


def test_module_04_error_shapes():
    client = TestClient(app, raise_server_exceptions=False)

    # 1. 404 Not Found error shape
    res_404 = client.get("/api/products/999")
    assert res_404.status_code == 404
    err_404 = res_404.json()
    assert "error" in err_404
    assert err_404["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert "message" in err_404["error"]
    assert "details" in err_404["error"]

    # 2. 422 Validation Error shape
    res_422 = client.post("/api/products", json={"name": "X", "price": -10.0, "stock": "bad"})
    assert res_422.status_code == 422
    err_422 = res_422.json()
    assert err_422["error"]["code"] == "VALIDATION_ERROR"
    assert len(err_422["error"]["details"]) >= 2

    # 3. 409 Conflict Error shape
    res_409 = client.post("/api/users?email=alex@example.com")
    assert res_409.status_code == 409
    err_409 = res_409.json()
    assert err_409["error"]["code"] == "USER_ALREADY_EXISTS"

    # 4. 500 Sanitized Error shape (No Stack Trace or File Path leak)
    res_500 = client.get("/api/crash-me")
    assert res_500.status_code == 500
    err_500 = res_500.json()
    assert err_500["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Ensure internal exception message is NOT leaked in response
    assert "abruptly" not in err_500["error"]["message"]
    assert "CRITICAL" not in err_500["error"]["message"]
