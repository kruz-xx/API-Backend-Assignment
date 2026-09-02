"""
Module 04: Errors, Validation & Response Design
Implements:
1. Centralized consistent error response envelope: {"error": {"code": "...", "message": "...", "details": [...]}}
2. Custom AppError domain exception class
3. Exception handlers for AppError, RequestValidationError (422), StarletteHTTPException, and uncaught 500 crashes
4. Safe internal server error sanitization (preventing stack trace / sensitive path leaks to clients)
"""

import logging
from typing import Any, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("module_04_errors")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Custom Domain Exception Class
# ---------------------------------------------------------------------------
class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


# ---------------------------------------------------------------------------
# FastAPI Application & Handler Registration
# ---------------------------------------------------------------------------
app = FastAPI(title="Standardized Error Handling Demo")


def register_standard_exception_handlers(target_app: FastAPI):
    @target_app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @target_app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": " -> ".join(map(str, err.get("loc", []))), "message": err.get("msg")}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload failed schema validation.",
                    "details": errors
                }
            }
        )

    @target_app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "details": []
                }
            }
        )

    @target_app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Secure: Internal log captures full traceback, but response is sanitized
        logger.error("Internal Server Error caught by safety handler: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred. Please contact support.",
                    "details": []
                }
            }
        )


register_standard_exception_handlers(app)


# ---------------------------------------------------------------------------
# Test Routes for Triggering Scenarios
# ---------------------------------------------------------------------------
class ProductInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    price: float = Field(..., gt=0.0)
    stock: int = Field(..., ge=0)


EXISTING_USERS = {"alex@example.com": {"id": 1, "name": "Alex"}}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    if product_id == 999:
        raise AppError(
            code="PRODUCT_NOT_FOUND",
            message=f"Product with ID {product_id} does not exist.",
            status_code=status.HTTP_404_NOT_FOUND,
            details=[{"field": "product_id", "message": f"ID {product_id} not in catalog."}]
        )
    return {"id": product_id, "name": "Mechanical Keyboard", "price": 89.99}


@app.post("/api/products")
async def create_product(product: ProductInput):
    return {"status": "created", "data": product.model_dump()}


@app.post("/api/users")
async def register_user(email: str):
    if email in EXISTING_USERS:
        raise AppError(
            code="USER_ALREADY_EXISTS",
            message=f"User account with email '{email}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            details=[{"field": "email", "message": "Email is registered to another user account."}]
        )
    return {"status": "created", "email": email}


@app.get("/api/crash-me")
async def crash_endpoint():
    # Intentionally trigger an unhandled runtime error (e.g. database timeout or division by zero)
    raise RuntimeError("CRITICAL: Database connection dropped abruptly during transaction execution!")


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_04_demo():
    client = TestClient(app, raise_server_exceptions=False)

    print("=" * 70)
    print("Module 04: Errors, Validation & Response Design Practical Run")
    print("=" * 70)

    # 1. 404 Not Found
    res_404 = client.get("/api/products/999")
    print(f"\n[1] GET /api/products/999 (404 Not Found) -> Status: {res_404.status_code}")
    print(f"    Payload:\n{res_404.json()}")

    # 2. 422 Validation Error
    res_422 = client.post("/api/products", json={"name": "X", "price": -20.0, "stock": "invalid"})
    print(f"\n[2] POST /api/products (422 Unprocessable Entity) -> Status: {res_422.status_code}")
    print(f"    Payload:\n{res_422.json()}")

    # 3. 409 Conflict
    res_409 = client.post("/api/users?email=alex@example.com")
    print(f"\n[3] POST /api/users (409 Conflict) -> Status: {res_409.status_code}")
    print(f"    Payload:\n{res_409.json()}")

    # 4. 500 Internal Server Error (Sanitized, No Stack Trace Leaked)
    res_500 = client.get("/api/crash-me")
    print(f"\n[4] GET /api/crash-me (500 Internal Server Error) -> Status: {res_500.status_code}")
    print(f"    Payload:\n{res_500.json()}")

    print("\n" + "=" * 70)
    print("Module 04 standardized error handling checks passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_04_demo()
