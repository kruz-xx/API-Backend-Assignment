"""
Tests for Module 02: First API & Book CRUD Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_02_first_api import (
    app,
    demonstrate_serialization,
    reset_state
)


def test_module_02_health_and_parameters():
    reset_state()
    client = TestClient(app)

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    # Path parameter
    res_path = client.get("/items/1")
    assert res_path.status_code == 200
    assert res_path.json()["name"] == "Clean Code"

    # Query parameter filtering
    res_query = client.get("/items?category=books&limit=5")
    assert res_query.status_code == 200
    assert res_query.json()["count"] == 2

    # Request body with generated ID
    res_body = client.post("/items", json={"name": "Headphones", "category": "audio", "price": 99.0})
    assert res_body.status_code == 201
    assert "id" in res_body.json()


def test_module_02_serialization_logic():
    parsed_dict, outgoing_json_str = demonstrate_serialization()
    assert isinstance(parsed_dict, dict)
    assert parsed_dict["title"] == "The Pragmatic Programmer"
    assert "tax" in parsed_dict
    assert isinstance(outgoing_json_str, str)
    assert "tax" in outgoing_json_str


def test_module_02_pydantic_validation_and_crud():
    reset_state()
    client = TestClient(app)

    # Validation rejection (422) for empty title and negative price
    res_invalid = client.post("/books", json={"title": "", "author": "Author", "price": -5.0})
    assert res_invalid.status_code == 422

    # 1. CREATE (201)
    res_create = client.post(
        "/books",
        json={"title": "Fluent Python", "author": "Luciano Ramalho", "price": 49.99, "published_year": 2022}
    )
    assert res_create.status_code == 201
    book_id = res_create.json()["id"]

    # 2. READ ALL (200)
    res_list = client.get("/books")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 3. READ ONE (200)
    res_get = client.get(f"/books/{book_id}")
    assert res_get.status_code == 200
    assert res_get.json()["title"] == "Fluent Python"

    # 4. UPDATE (200)
    res_update = client.patch(f"/books/{book_id}", json={"price": 44.99})
    assert res_update.status_code == 200
    assert res_update.json()["price"] == 44.99

    # 5. DELETE (204)
    res_del = client.delete(f"/books/{book_id}")
    assert res_del.status_code == 204

    # 6. Verify 404
    res_get_deleted = client.get(f"/books/{book_id}")
    assert res_get_deleted.status_code == 404
