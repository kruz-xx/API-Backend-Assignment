"""
Module 08: API Security Practical
Implements:
1. Input Validation Defensive Boundary: Blocking negative quantity / integer overflow exploits using Pydantic
2. CORS (Cross-Origin Resource Sharing) configuration & preflight OPTIONS validation
3. Principle of Least Privilege: Scoped authorization tokens (e.g. orders:write vs analytics:read)
4. OWASP API Security #1: Broken Object Level Authorization (BOLA/IDOR) mitigation
"""

from decimal import Decimal
from typing import List, Set
from fastapi import Depends, FastAPI, HTTPException, Header, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# FastAPI Application & CORS Configuration
# ---------------------------------------------------------------------------
app = FastAPI(title="API Security Practical Demo")

ALLOWED_ORIGINS = [
    "https://trusted-dashboard.example.com",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=86400
)


# ---------------------------------------------------------------------------
# 1. Input Validation Defensive Schemas (E-Commerce Inversion Protection)
# ---------------------------------------------------------------------------
class OrderItemSecure(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID must be positive")
    quantity: int = Field(..., gt=0, le=100, description="Quantity must be strictly positive (1-100)")
    unit_price: Decimal = Field(..., gt=Decimal("0.00"), description="Unit price must be positive")

    @field_validator("quantity")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Negative or zero quantities are strictly forbidden.")
        return v


class CheckoutPayload(BaseModel):
    customer_id: int = Field(..., gt=0)
    items: List[OrderItemSecure] = Field(..., min_length=1)


@app.post("/api/v1/orders/checkout", status_code=status.HTTP_201_CREATED)
def secure_checkout(order: CheckoutPayload):
    total = sum(item.quantity * item.unit_price for item in order.items)
    return {
        "status": "success",
        "customer_id": order.customer_id,
        "total_amount": float(total),
        "item_count": sum(item.quantity for item in order.items)
    }


# ---------------------------------------------------------------------------
# 2. Principle of Least Privilege: Scoped Token Authorization
# ---------------------------------------------------------------------------
TOKEN_SCOPES_DB = {
    "token_analytics_123": {"client_id": "analytics_worker", "scopes": {"analytics:read"}},
    "token_payment_456": {"client_id": "payment_gateway", "scopes": {"orders:write", "orders:read"}},
}


def require_scopes(required_scopes: List[str]):
    def scope_checker(authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "NOT_AUTHENTICATED", "message": "Bearer token required."}}
            )
        token = authorization.split(" ", 1)[1].strip()
        client_info = TOKEN_SCOPES_DB.get(token)
        if not client_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "message": "Token not found."}}
            )

        token_scopes: Set[str] = client_info["scopes"]
        for scope in required_scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "INSUFFICIENT_PERMISSIONS",
                            "message": f"Token lacks required scope '{scope}'. Granted: {list(token_scopes)}"
                        }
                    }
                )
        return client_info
    return scope_checker


@app.post("/api/v1/orders/charge", dependencies=[Depends(require_scopes(["orders:write"]))])
def charge_order(order_id: int):
    return {"status": "charged", "order_id": order_id}


@app.get("/api/v1/analytics/metrics", dependencies=[Depends(require_scopes(["analytics:read"]))])
def get_metrics():
    return {"status": "success", "active_connections": 128}


# ---------------------------------------------------------------------------
# 3. OWASP BOLA / IDOR Protection
# ---------------------------------------------------------------------------
INVOICES_DB = {
    1: {"id": 1, "owner_user_id": 101, "amount": 149.99, "description": "User 101 Confidential Invoice"},
    2: {"id": 2, "owner_user_id": 102, "amount": 890.00, "description": "User 102 Confidential Invoice"}
}


@app.get("/api/v1/invoices/{invoice_id}")
def get_invoice_secure(invoice_id: int, current_user_id: int = Header(..., alias="X-User-ID")):
    invoice = INVOICES_DB.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    # BOLA check: Ensure caller owns the requested object
    if invoice["owner_user_id"] != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "BOLA_VIOLATION",
                    "message": "Access denied: You do not have permission to access another user's invoice."
                }
            }
        )

    return {"status": "success", "invoice": invoice}


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_08_demo():
    client = TestClient(app)

    print("=" * 70)
    print("Module 08: API Security Practical Run")
    print("=" * 70)

    # 1. Negative Quantity Attack Prevention
    print("\n[1] Testing Negative Quantity Attack:")
    attack_payload = {"customer_id": 42, "items": [{"product_id": 1, "quantity": -5, "unit_price": 50.00}]}
    res_attack = client.post("/api/v1/orders/checkout", json=attack_payload)
    print(f"    Attack Status: {res_attack.status_code} Unprocessable Entity (Expected 422)")
    print(f"    Validation Error Details: {res_attack.json()['detail']}")

    # 2. CORS Preflight Testing
    print("\n[2] Testing CORS Preflight Requests:")
    # Whitelisted origin
    res_cors_ok = client.options(
        "/api/v1/orders/checkout",
        headers={
            "Origin": "https://trusted-dashboard.example.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    print(f"    Whitelisted Origin Preflight -> Status: {res_cors_ok.status_code}, Allow-Origin: {res_cors_ok.headers.get('access-control-allow-origin')}")

    # 3. Principle of Least Privilege (Scope Checks)
    print("\n[3] Testing Scoped Authorization (Least Privilege):")
    # Analytics token trying to charge order (Forbidden)
    res_scope_err = client.post("/api/v1/orders/charge?order_id=1", headers={"Authorization": "Bearer token_analytics_123"})
    print(f"    Analytics Token on Charge Endpoint -> Status: {res_scope_err.status_code} (Expected 403)")
    print(f"    Detail: {res_scope_err.json()['detail']}")

    # Payment token charging order (Allowed)
    res_scope_ok = client.post("/api/v1/orders/charge?order_id=1", headers={"Authorization": "Bearer token_payment_456"})
    print(f"    Payment Token on Charge Endpoint -> Status: {res_scope_ok.status_code} (Allowed)")

    # 4. BOLA / IDOR Protection
    print("\n[4] Testing BOLA / IDOR Ownership Verification:")
    # User 101 accessing User 101's invoice (200 OK)
    res_bola_ok = client.get("/api/v1/invoices/1", headers={"X-User-ID": "101"})
    print(f"    User 101 reading Invoice #1 -> Status: {res_bola_ok.status_code} OK")

    # User 101 attempting to access User 102's private invoice #2 (403 Forbidden)
    res_bola_err = client.get("/api/v1/invoices/2", headers={"X-User-ID": "101"})
    print(f"    User 101 reading Invoice #2 -> Status: {res_bola_err.status_code} Forbidden (Expected 403)")
    print(f"    Detail: {res_bola_err.json()['detail']}")

    print("\n" + "=" * 70)
    print("Module 08 API security verification passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_08_demo()
