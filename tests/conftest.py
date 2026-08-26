from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.auth import create_access_token, hash_password, users_db
from src.routers.products import products_db
from src.routers.orders import orders_db


@pytest.fixture(autouse=True)
def reset_database_state():
    """
    Resets the in-memory database fixtures before every test run.
    """
    users_db.clear()
    orders_db.clear()

    # Seed Admin User
    admin_user = {
        "id": 1,
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "hashed_password": hash_password("AdminPass123!"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    users_db["admin@example.com"] = admin_user

    # Seed Regular Customer User
    customer_user = {
        "id": 2,
        "email": "customer@example.com",
        "full_name": "John Doe",
        "role": "customer",
        "hashed_password": hash_password("CustomerPass123!"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    users_db["customer@example.com"] = customer_user

    # Reset sample products
    products_db.clear()
    products_db[1] = {
        "id": 1,
        "name": "Mechanical Keyboard",
        "description": "Tactile RGB mechanical keyboard.",
        "price": 89.99,
        "stock": 20,
        "category": "Electronics",
        "created_at": datetime.now(timezone.utc)
    }
    products_db[2] = {
        "id": 2,
        "name": "Wireless Mouse",
        "description": "Ergonomic Bluetooth mouse.",
        "price": 39.99,
        "stock": 35,
        "category": "Electronics",
        "created_at": datetime.now(timezone.utc)
    }

    yield


@pytest.fixture
def client():
    """
    Pytest fixture yielding Starlette/FastAPI TestClient.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin@example.com", "role": "admin"})


@pytest.fixture
def customer_token():
    return create_access_token({"sub": "customer@example.com", "role": "customer"})
