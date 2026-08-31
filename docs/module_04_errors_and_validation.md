# Module 04 — Errors, Validation & Response Design

## Overview
Designing predictable, standardized JSON error responses, handling FastAPI request validation errors (422 Unprocessable Entity), raising custom business domain exceptions, implementing centralized global exception handlers, and securing internal server error diagnostics.

---

## Conceptual Questions & Implementation Notes

### 1. Consistent Error Response Shape
> Design a **consistent error response shape** for your whole API (e.g. `{"error": {"code": "ITEM_NOT_FOUND", "message": "..."}}`) and use it everywhere instead of ad-hoc error messages. Explain why consistency here matters for anyone building a client against your API.

**Answer & Schema Design:**

**Why Consistency matters:**

1. Unified Client-Side Error Interceptor:
   Frontend/mobile apps can parse errors using a single generic error handler rather than writing custom parsing logic for every endpoint. 

2. Machine-readable code:
   Clients make programmatic decisions based on constant enum codes.
   E.g.: TOOKEN_EXPIRED triggers refresh token flow;
         INSUFFICIENT_FUNDS prompts top-up modal rather than fragile regex matching on human-readable error messages.

3. Form-Level Validation Mapping (details): 
   The details array provides field-level error mappings that frontend forms can bind directly to UI input components.

4. Internationalization (i18n): 
   Client applications can translate messages based on error code keys without relying on server-side localized text

**Standardized Error Response Shape**

```json
{
  "error": {
    "code": "ITEM_NOT_FOUND",
    "message": "Product with ID 999 does not exist.",
    "details": [
      {
        "field": "product_id",
        "message": "No active catalog entry matching ID 999."
      }
    ]
  }
}

```
---

### 2. Proper HTTP Error Handling & Status Codes
> Implement proper error handling: return `404` when an item doesn't exist (not a `500` crash), `400`/`422` for invalid input, `409` for a conflict (e.g. creating a duplicate). Demonstrate each with `curl`.

**Answer & Examples:**

**A. 404 Not Found (Resource Does Not Exist):**
Triggered when requesting an ID that does not exist in the database (not a 500 server crash).

Command:
```bash
curl -i http://127.0.0.1:8000/api/v1/products/999
Response (404 Not Found):
http
HTTP/1.1 404 Not Found
content-type: application/json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID 999 does not exist.",
    "details": []
  }
}
```
**B. 422 Unprocessable Entity / 400 Bad Request (Invalid Input / Schema Validation):**
Triggered when the client sends missing required fields, wrong data types, or violated constraints (e.g., negative price).

Command:
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name": "X", "price": -15.0, "stock": "invalid_number"}'
Response (422 Unprocessable Entity):
http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request payload failed schema validation.",
    "details": [
      {"field": "body -> name", "message": "String should have at least 2 characters" },
      {"field": "body -> price", "message": "Input should be greater than 0" },
      {"field": "body -> stock", "message": "Input should be a valid integer" }
    ]
  }
}
```
**C. 409 Conflict (Duplicate Entry / State Collision):**
Triggered when attempting to create a resource with a unique attribute that already exists (e.g., duplicate user email or SKU).

Command:
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "[EMAIL_ADDRESS]", "full_name": "Alex Smith", "password": "securepassword123"}'
Response (409 Conflict):
http
HTTP/1.1 409 Conflict
content-type: application/json
{
  "error": {
    "code": "USER_ALREADY_EXISTS",
    "message": "A user account with email 'alex@example.com' already exists.",
    "details": []
  }

```
---

### 3. Client Errors (4xx) vs Server Errors (5xx) & The "Silent 200" Antipattern
> Explain the difference between an error that's the **client's fault** (`4xx`) and the **server's fault** (`5xx`), and why silently returning `200` on failure (a very common bad practice) breaks every client integration built against your API.

**Answer:**

**4xx Client Error vs 5xx Server Error**

**4xx (Client's Fault):**
The request was invalid, unauthorized, malformed, or asked for something unavailable. The client must change the request before retrying.

**5xx (Server's Fault):**
The server crashed, database connection dropped, or an unhandled bug occurred while attempting to process a valid request. The client may retry after some time with backoff.

**Why Silently Returning 200 OK on Failure Breaks Client Integrations:**

- Breaks Standard HTTP Libraries: Frameworks like Axios, Fetch API, and Python requests automatically throw exceptions or route to .catch() blocks for non-2xx status codes (response.ok === false). Returning 200 OK forces client code to manually inspect response bodies every time.

- Pollutes Caching Proxies and CDNs: CDNs and caching layers (Cloudflare, Varnish) cache 200 OK responses by default. A cached error message served as 200 OK will be delivered to other users as valid data.

- Blinds Monitoring & Alerting Systems: Observability tools (Datadog, Prometheus, Sentry, AWS CloudWatch) monitor error budgets (SLOs/SLAs) via HTTP status code rates. A silent 200 masks critical outages and makes production debugging impossible.

---

### 4. Global Exception Handling in FastAPI
> Add global exception handling (e.g. FastAPI's exception handlers) so an unexpected crash returns a clean `500` with your standard error shape instead of leaking a stack trace to the client.

**Answer & Implementation:**

Global Exception Handling in FastAPI is a way to handle errors that are not caught by the exception handlers of individual routes.

```python
import logging
from typing import Any, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Base Custom Application Error
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
# Centralized Exception Registration
# ---------------------------------------------------------------------------
def register_exception_handlers(app: FastAPI) -> None:
    
    # 1. Handle Domain Business Errors (AppError)
    @app.exception_handler(AppError)
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

    # 2. Handle Pydantic / FastAPI Validation Errors (422)
    @app.exception_handler(RequestValidationError)
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

    # 3. Handle Framework HTTP Exceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": []
                }
            }
        )

    # 4. Catch-All Global Handler for Unexpected 500 Crashes (No Stack Trace Leak)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled Internal Server Error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": []
                }
            }
        )

```

Output:
```bash
curl -i http://127.0.0.1:8000/api/v1/users

```
```http

HTTP/1.1 500 Internal Server Error
content-type: application/json

{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected internal server error occurred.",
    "details": []
  }
}


```
---

### 5. Security & Preventing Internal Details Leaks
> Explain why you should **never** leak internal details (stack traces, database errors, internal file paths) in an API error response to an external client — tie this back to security (Module 8).

**Answer:**

Why Internal Details Must Never Be Returned in Responses

1. **Information Disclosure (CWE-209 / OWASP API Security #8):**
- Stack traces reveal server operating system, internal file paths (/app/src/services/db.py), library versions (e.g., FastAPI 0.110.0, SQLAlchemy 2.0.18), and framework internals.
- Attackers use this blueprint to identify unpatched vulnerabilities and known CVEs.

2. **Database Schema & Injection Assistance:**
- Leaking raw database driver errors (e.g., psycopg2.errors.UniqueViolation, table names, column names) helps attackers construct targeted SQL Injection or exploit relational constraints.

3. **Credential & Secret Exposure:**
- Unhandled exception traces may print environment variable dictionaries, database connection strings, or third-party API keys in traceback local variable frames.

**Secure Production Best Practice:**

- Log full tracebacks and diagnostics internally to secured logging pipelines (CloudWatch, Datadog, ELK).
- Assign a unique request_id / correlation_id header (e.g., X-Request-ID: e62b71ab-9df4) to the response so developers can look up the internal logs without exposing raw traces to clients.


---

