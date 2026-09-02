"""
Tests for Module 01: HTTP Fundamentals Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_01_http_client import demo_app, run_http_demonstration


def test_module_01_http_verbs_and_headers():
    client = TestClient(demo_app)

    # 1. GET Request with headers
    res_get = client.get("/items/1", headers={"User-Agent": "PytestClient", "Accept": "application/json"})
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "success"
    assert res_get.json()["received_headers"]["User-Agent"] == "PytestClient"

    # 2. POST Request with Authorization header
    res_post = client.post(
        "/items",
        json={"name": "Gaming Mouse", "price": 39.99},
        headers={"Authorization": "Bearer token_abc"}
    )
    assert res_post.status_code == 201
    assert res_post.json()["auth_received"] is True
    new_id = res_post.json()["data"]["id"]

    # 3. PUT Request (Replace full resource)
    res_put = client.put(f"/items/{new_id}", json={"name": "Replaced Mouse", "price": 45.00})
    assert res_put.status_code == 200
    assert res_put.json()["data"]["name"] == "Replaced Mouse"

    # 4. PATCH Request (Partial update)
    res_patch = client.patch(f"/items/{new_id}", json={"price": 42.50})
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["price"] == 42.50

    # 5. HEAD Request (Headers only)
    res_head = client.head("/items/1")
    assert res_head.status_code == 200
    assert res_head.headers.get("x-item-exists") == "true"
    assert len(res_head.content) == 0

    # 6. OPTIONS Request
    res_options = client.options("/items")
    assert res_options.status_code == 200
    assert "OPTIONS" in res_options.headers.get("allow")

    # 7. DELETE Request
    res_delete = client.delete(f"/items/{new_id}")
    assert res_delete.status_code == 204

    # 8. 404 on deleted item
    res_404 = client.get(f"/items/{new_id}")
    assert res_404.status_code == 404


def test_module_01_script_execution():
    results = run_http_demonstration()
    assert results["get_status"] == 200
    assert results["post_status"] == 201
    assert results["delete_status"] == 204
    assert results["deleted_get_status"] == 404
