"""
Tests for Module 03: REST Principles, Pagination & Versioning Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_03_rest_api import app


def test_module_03_pagination():
    client = TestClient(app)

    # Valid page 1
    res = client.get("/api/items?page=1&page_size=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3
    assert data["pagination"]["total_count"] == 8
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["has_next"] is True
    assert data["pagination"]["has_prev"] is False
    assert data["pagination"]["next_page"] == 2

    # Out of range page (404)
    res_out = client.get("/api/items?page=99&page_size=10")
    assert res_out.status_code == 404


def test_module_03_filtering_sorting_searching():
    client = TestClient(app)

    # Search + filter + sort descending
    res = client.get("/api/items?category=books&search=harry&sort=-price")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    assert items[0]["price"] >= items[1]["price"]
    assert "Harry Potter" in items[0]["name"]


def test_module_03_api_versioning_schemas():
    client = TestClient(app)

    # V1 Flat schema
    res_v1 = client.get("/api/v1/items")
    assert res_v1.status_code == 200
    first_v1 = res_v1.json()[0]
    assert "id" in first_v1
    assert "name" in first_v1
    assert "price" in first_v1
    assert isinstance(first_v1["price"], float)

    # V2 Restructured schema with nested pricing and availability flag
    res_v2 = client.get("/api/v2/items")
    assert res_v2.status_code == 200
    first_v2 = res_v2.json()[0]
    assert "title" in first_v2
    assert "pricing" in first_v2
    assert "amount" in first_v2["pricing"]
    assert "formatted" in first_v2["pricing"]
    assert "in_stock" in first_v2
