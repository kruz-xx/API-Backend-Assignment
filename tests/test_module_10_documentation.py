"""
Tests for Module 10: API Documentation & OpenAPI Specification Practical
"""

from fastapi.testclient import TestClient
from src.main import app as main_app
from src.practicals.module_10_docs_demo import (
    app as docs_demo_app,
    run_module_10_demo
)


def test_module_10_openapi_schema_generation():
    client = TestClient(docs_demo_app)

    # 1. OpenAPI JSON Schema endpoint
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert schema["openapi"].startswith("3.")
    assert "info" in schema
    assert schema["info"]["title"] == "Enterprise E-Commerce API"
    assert "/products" in schema["paths"]
    assert "/health" in schema["paths"]

    # 2. Interactive Swagger UI & ReDoc HTML routes
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 200


def test_module_10_main_app_documentation():
    client = TestClient(main_app)
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert schema["info"]["title"] == "API Backend Assignment"
    assert "/graphql" in schema["paths"]
    assert "/health" in schema["paths"]


def test_module_10_runner_script():
    schema = run_module_10_demo()
    assert schema is not None
    assert len(schema["paths"]) >= 2
