"""
Tests for Module 09: Testing Strategies Practical
Demonstrates unit tests, external API mocking, and FastAPI dependency overrides.
"""

from unittest.mock import MagicMock, patch
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.testclient import TestClient
import httpx
from src.services.auth import hash_password, verify_password

# ---------------------------------------------------------------------------
# Target app for dependency override and external mocking tests
# ---------------------------------------------------------------------------
demo_test_app = FastAPI()


def get_current_user_stub(authorization: str = Header(None)):
    raise HTTPException(status_code=401, detail="Real authentication required.")


@demo_test_app.get("/admin-panel")
def admin_panel(user: dict = Depends(get_current_user_stub)):
    return {"status": "access_granted", "user": user}


def fetch_external_fx_rates() -> dict:
    with httpx.Client(timeout=5.0) as client:
        res = client.get("https://api.externalfx.com/v1/rates")
        res.raise_for_status()
        return res.json()


@demo_test_app.get("/fx/usd-to-eur")
def convert_usd_to_eur(amount: float):
    rates = fetch_external_fx_rates()
    rate = rates.get("EUR", 0.92)
    return {"usd": amount, "eur": round(amount * rate, 2)}


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
def test_unit_password_hashing():
    """Unit test: Tests hash_password and verify_password in complete isolation."""
    raw = "MySecurePassword123!"
    hashed = hash_password(raw)
    assert isinstance(hashed, str)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_dependency_override_bypassing_auth():
    """Integration test using FastAPI app.dependency_overrides to inject mock user."""
    mock_admin_user = {"id": 1, "email": "mockadmin@example.com", "role": "admin"}

    def override_auth():
        return mock_admin_user

    demo_test_app.dependency_overrides[get_current_user_stub] = override_auth

    try:
        client = TestClient(demo_test_app)
        res = client.get("/admin-panel")
        assert res.status_code == 200
        assert res.json()["user"]["email"] == "mockadmin@example.com"
    finally:
        demo_test_app.dependency_overrides.clear()


def test_mocking_external_api_call():
    """Tests mocking an external HTTP dependency to guarantee deterministic CI runs."""
    mock_fx_payload = {"USD": 1.0, "EUR": 0.85, "GBP": 0.75}

    with patch("tests.test_module_09_testing_strategies.fetch_external_fx_rates", return_value=mock_fx_payload):
        client = TestClient(demo_test_app)
        res = client.get("/fx/usd-to-eur?amount=100")
        assert res.status_code == 200
        assert res.json()["eur"] == 85.0
