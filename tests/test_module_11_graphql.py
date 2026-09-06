"""
Tests for Module 11: GraphQL Practical
"""

from fastapi.testclient import TestClient
from src.main import app as main_app
from src.practicals.module_11_graphql_app import app as gql_demo_app


def test_module_11_graphql_field_selection():
    client = TestClient(gql_demo_app)

    query = """
    query {
        products {
            id
            name
            price
        }
    }
    """
    res = client.post("/graphql", json={"query": query})
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    products = data["data"]["products"]
    assert len(products) >= 1
    # Verifies only requested fields are returned
    first_item = products[0]
    assert "id" in first_item
    assert "name" in first_item
    assert "price" in first_item
    assert "description" not in first_item


def test_module_11_graphql_mutations():
    client = TestClient(gql_demo_app)

    mutation = """
    mutation {
        createProduct(name: "Mechanical Keycaps", price: 29.99, stock: 40, category: "Accessories") {
            id
            name
            price
        }
    }
    """
    res = client.post("/graphql", json={"query": mutation})
    assert res.status_code == 200
    data = res.json()
    assert data["data"]["createProduct"]["name"] == "Mechanical Keycaps"


def test_module_11_main_app_graphql_route():
    client = TestClient(main_app)

    query = """
    query {
        products {
            id
            name
        }
    }
    """
    res = client.post("/graphql", json={"query": query})
    assert res.status_code == 200
    assert "data" in res.json()
