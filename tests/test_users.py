def test_health_check(client):
    """
    Test GET /health endpoint (Module 02).
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_user_registration_success(client):
    """
    Test valid user registration.
    """
    payload = {
        "email": "newuser@example.com",
        "full_name": "New Tester",
        "password": "Password123!",
        "role": "customer"
    }
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert "id" in data
    assert "password" not in data  # Never leak password hash


def test_user_registration_duplicate_email(client):
    """
    Test duplicate registration triggers 409 Conflict.
    """
    payload = {
        "email": "customer@example.com",
        "full_name": "Duplicate User",
        "password": "Password123!",
        "role": "customer"
    }
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "USER_ALREADY_EXISTS"


def test_user_login_success(client):
    """
    Test valid login returns Bearer token.
    """
    payload = {
        "email": "customer@example.com",
        "password": "CustomerPass123!"
    }
    response = client.post("/api/v1/users/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_invalid_password(client):
    """
    Test login with wrong credentials returns 401.
    """
    payload = {
        "email": "customer@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/users/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_get_current_user_profile(client, customer_token):
    """
    Test GET /api/v1/users/me with Bearer token.
    """
    headers = {"Authorization": f"Bearer {customer_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "customer@example.com"
    assert data["role"] == "customer"


def test_get_current_user_unauthorized(client):
    """
    Test accessing protected endpoint without token returns 401.
    """
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "MISSING_CREDENTIALS"
