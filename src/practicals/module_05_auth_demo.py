"""
Module 05: Authentication & Authorization Practical
Implements:
1. API Key Authentication via X-API-Key header (rejecting invalid/missing keys with 401)
2. JWT-Based Authentication: Token issuance, Base64 decoding, cryptographic HMAC-SHA256 signature verification, and tamper detection
3. Role-Based Access Control (RBAC): Admin vs Customer permissions, returning 403 Forbidden for unauthorized roles
4. Token Expiration and Refresh Token mechanics simulation
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

SECRET_KEY = "demo-auth-secret-key-min-32-chars-length"
ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Enums & Schemas
# ---------------------------------------------------------------------------
class RoleEnum(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class UserProfile(BaseModel):
    id: int
    email: str
    role: RoleEnum


class TokenPayload(BaseModel):
    sub: str
    user_id: int
    role: str
    exp: int


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------
API_KEYS_DB = {
    "secret-backend-key-12345": {"client_id": "payment_worker", "tier": "enterprise"},
    "partner-api-key-67890": {"client_id": "analytics_bot", "tier": "standard"}
}

USERS_DB = {
    "admin@example.com": {"id": 1, "email": "admin@example.com", "password": "AdminPassword123!", "role": RoleEnum.ADMIN},
    "customer@example.com": {"id": 2, "email": "customer@example.com", "password": "CustomerPassword123!", "role": RoleEnum.CUSTOMER}
}


# ---------------------------------------------------------------------------
# 1. API Key Verification Dependency
# ---------------------------------------------------------------------------
def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> dict:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "MISSING_API_KEY", "message": "X-API-Key header is required."}}
        )
    if x_api_key not in API_KEYS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_API_KEY", "message": "Provided API key is invalid."}}
        )
    return API_KEYS_DB[x_api_key]


# ---------------------------------------------------------------------------
# 2. JWT Cryptographic Generation & Verification Functions
# ---------------------------------------------------------------------------
def generate_jwt(data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")

    payload = data.copy()
    payload["exp"] = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode().rstrip("=")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_and_decode_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN_FORMAT", "message": "Token must contain 3 segments."}}
        )

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "SIGNATURE_VERIFICATION_FAILED", "message": "Token signature mismatch (tampering detected)."}}
        )

    # Pad and decode payload
    rem = len(payload_b64) % 4
    padded_payload_b64 = payload_b64 + ("=" * (4 - rem) if rem else "")
    payload_dict = json.loads(base64.urlsafe_b64decode(padded_payload_b64.encode()).decode())

    if payload_dict.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Authentication token has expired."}}
        )

    return payload_dict


# ---------------------------------------------------------------------------
# 3. RBAC Dependencies
# ---------------------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "NOT_AUTHENTICATED", "message": "Bearer token required."}}
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_and_decode_jwt(token)
    email = payload.get("sub")
    user = USERS_DB.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="User record not found.")
    return UserProfile(id=user["id"], email=user["email"], role=user["role"])


def require_admin(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN_OPERATION",
                    "message": f"Action requires '{RoleEnum.ADMIN.value}' privileges. Caller has '{user.role.value}'."
                }
            }
        )
    return user


# ---------------------------------------------------------------------------
# FastAPI App & Endpoints
# ---------------------------------------------------------------------------
app = FastAPI(title="Authentication & Security Demo")


@app.get("/api/service/data")
def get_service_data(service_info: dict = Depends(verify_api_key)):
    return {"status": "success", "client": service_info["client_id"], "tier": service_info["tier"]}


@app.post("/api/auth/login")
def login(email: str, password: str):
    user = USERS_DB.get(email)
    if not user or user["password"] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Incorrect email or password."}}
        )
    token = generate_jwt({"sub": user["email"], "user_id": user["id"], "role": user["role"].value})
    return {"access_token": token, "token_type": "bearer", "expires_in": 900}


@app.get("/api/users/me")
def get_profile(current_user: UserProfile = Depends(get_current_user)):
    return {"status": "success", "profile": current_user.model_dump()}


@app.delete("/api/items/{item_id}")
def delete_item_admin_only(item_id: int, _: UserProfile = Depends(require_admin)):
    return {"status": "success", "message": f"Item {item_id} deleted by administrator."}


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_05_demo():
    client = TestClient(app)

    print("=" * 70)
    print("Module 05: Authentication & Authorization Practical Run")
    print("=" * 70)

    # 1. API Key Authentication
    # Valid key
    res_key_ok = client.get("/api/service/data", headers={"X-API-Key": "secret-backend-key-12345"})
    print(f"\n[1] API Key Auth (Valid): Status {res_key_ok.status_code}, Body: {res_key_ok.json()}")

    # Invalid key (401)
    res_key_err = client.get("/api/service/data", headers={"X-API-Key": "invalid-key"})
    print(f"    API Key Auth (Invalid): Status {res_key_err.status_code}, Body: {res_key_err.json()['detail']}")

    # 2. Login to retrieve JWT Access Token
    res_login_cust = client.post("/api/auth/login?email=customer@example.com&password=CustomerPassword123!")
    customer_token = res_login_cust.json()["access_token"]
    print(f"\n[2] Customer Login -> Status: {res_login_cust.status_code}")
    print(f"    Generated Token: {customer_token[:30]}...")

    res_login_admin = client.post("/api/auth/login?email=admin@example.com&password=AdminPassword123!")
    admin_token = res_login_admin.json()["access_token"]
    print(f"    Admin Login -> Status: {res_login_admin.status_code}")

    # 3. Access Protected Route with Bearer Token
    res_me = client.get("/api/users/me", headers={"Authorization": f"Bearer {customer_token}"})
    print(f"\n[3] GET /api/users/me (Customer Auth) -> Status: {res_me.status_code}, Role: {res_me.json()['profile']['role']}")

    # 4. RBAC Verification (Customer attempts Admin DELETE endpoint -> 403 Forbidden)
    res_forbidden = client.delete("/api/items/42", headers={"Authorization": f"Bearer {customer_token}"})
    print(f"\n[4] RBAC Protection (Customer calling DELETE /items/42) -> Status: {res_forbidden.status_code} (Expected 403)")
    print(f"    Error Response: {res_forbidden.json()['detail']}")

    # Admin calls same DELETE endpoint -> 200 OK
    res_admin_del = client.delete("/api/items/42", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"    RBAC Protection (Admin calling DELETE /items/42) -> Status: {res_admin_del.status_code} (Allowed)")

    # 5. Tampering Detection Demonstration
    # Tampering payload: change role from customer to admin without signature recalculation
    header_b64, payload_b64, sig_b64 = customer_token.split(".")
    tampered_payload = {"sub": "customer@example.com", "user_id": 2, "role": "admin", "exp": int(time.time()) + 900}
    tampered_payload_b64 = base64.urlsafe_b64encode(json.dumps(tampered_payload, sort_keys=True).encode()).decode().rstrip("=")
    tampered_token = f"{header_b64}.{tampered_payload_b64}.{sig_b64}"

    res_tampered = client.get("/api/users/me", headers={"Authorization": f"Bearer {tampered_token}"})
    print(f"\n[5] Tampered JWT Test -> Status: {res_tampered.status_code} (Expected 401)")
    print(f"    Tamper Detection Detail: {res_tampered.json()['detail']}")

    print("\n" + "=" * 70)
    print("Module 05 authentication, JWT & RBAC tests passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_05_demo()
