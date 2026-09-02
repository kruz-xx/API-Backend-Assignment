# Module 04 — Errors, Validation & Response Design

## Overview
Designing predictable, standardized JSON error responses, handling FastAPI request validation errors (422 Unprocessable Entity), raising custom business domain exceptions, implementing centralized global exception handlers, and securing internal server error diagnostics.

---

## Conceptual Questions & Answers

### 1. Consistent Error Response Shape
> Design a consistent error response shape for your whole API (e.g. `{"error": {"code": "ITEM_NOT_FOUND", "message": "..."}}`) and use it everywhere. Explain why consistency matters.

**Why Consistency Matters:**
1. **Unified Client-Side Interceptors**: Frontends, mobile clients, and SDKs can parse all error responses through a single centralized error interceptor instead of ad-hoc per-endpoint error logic.
2. **Machine-Readable Codes**: Constant error codes (e.g., `TOKEN_EXPIRED`, `INSUFFICIENT_STOCK`) allow client applications to trigger programmatic remediation flows (such as token refreshes or checkout prompts) without fragile regex matching against localized human-readable messages.
3. **Form-Level Validation Mapping**: Standardized `details` lists (with `field` and `message`) allow UI frameworks to bind validation messages directly to specific form input elements.
4. **Internationalization (i18n)**: Clients can localize user-facing messages based on stable machine-readable error codes.

---

### 2. Proper HTTP Error Handling & Status Codes
> Implement proper error handling: return `404` when an item doesn't exist (not a `500` crash), `400`/`422` for invalid input, `409` for a conflict (e.g. duplicate email).

- `404 Not Found`: Resource identifier does not exist in the database.
- `422 Unprocessable Entity` / `400 Bad Request`: Payload violates schema rules (negative values, missing fields, invalid types).
- `409 Conflict`: Request conflicts with current database state (e.g., duplicate user email or existing unique SKU).

---

### 3. Client Errors (4xx) vs Server Errors (5xx) & The "Silent 200" Antipattern
> Explain the difference between client errors (`4xx`) and server errors (`5xx`), and why silently returning `200` on failure breaks client integrations.

**Why the "Silent 200" (Returning 200 OK with `{"success": false}`) is a Destructive Antipattern:**
1. **Breaks HTTP Client Libraries**: Libraries like Axios, Fetch API, and Python `requests` use HTTP status codes to trigger error handling (`response.ok === false` or `raise_for_status()`). A silent 200 bypasses `.catch()` blocks and requires manual body inspection on every call.
2. **Pollutes Caching Proxies and CDNs**: Proxies and CDNs cache 200 OK responses by default. A cached error payload returned with 200 OK will be served to other clients as valid data.
3. **Blinds Monitoring & Alerting**: Observability tools (Datadog, Sentry, Prometheus, CloudWatch) monitor service health using HTTP 4xx/5xx error rates. Silent 200 responses mask outages and hide operational incidents.

---

### 4. Global Exception Handling in FastAPI
> Add global exception handling so an unexpected crash returns a clean `500` with standard error shape instead of leaking a stack trace to the client.

Global exception handlers in FastAPI intercept uncaught exceptions before they exit the ASGI pipeline, logging the full traceback internally while sending a sanitized JSON response to the caller.

---

### 5. Security & Preventing Internal Details Leaks
> Explain why you should never leak internal details (stack traces, database errors, internal file paths) in an API error response.

**Risks of Leaking Internal Diagnostics (CWE-209 / OWASP API Security #8):**
1. **Stack Trace Disclosures**: Expose server operating systems, internal file directory paths, framework versions, and internal package names, providing attackers with a targeted blueprint for known CVE vulnerabilities.
2. **Database Engine Errors**: Leaking SQL driver syntax errors (e.g. PostgreSQL constraint violations or table names) aids attackers in constructing SQL injection vectors.
3. **Credential Leaks**: Unhandled tracebacks may display local stack frame variables containing database passwords, environment variables, or private API keys.

---

## Practical: Standardized Error Handling & Exception Middleware

### Implementation
**File:** [`src/practicals/module_04_error_handling.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_04_error_handling.py)  
**Middleware:** [`src/middlewares/error_handler.py`](file:///c:/office%20files/api-backend-assignment/src/middlewares/error_handler.py)  
**Tests:** [`tests/test_module_04_errors.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_04_errors.py)

Implemented:
1. Standardized error response envelope: `{"error": {"code": "...", "message": "...", "details": [...]}}`.
2. Custom domain exception `AppError` carrying machine codes, HTTP status codes, and field error lists.
3. Centralized exception handlers for:
   - `AppError` (Domain business exceptions)
   - `RequestValidationError` (Pydantic schema validation errors converted to standard shape)
   - `StarletteHTTPException` (Framework routing and HTTP exceptions)
   - `Exception` (Catch-all 500 handler that safely logs tracebacks internally while returning a sanitized response to the client).

### How I Ran It
```bash
python -m src.practicals.module_04_error_handling
```

### Testing
```bash
pytest tests/test_module_04_errors.py -v
```

### Result
```text
======================================================================
Module 04: Errors, Validation & Response Design Practical Run
======================================================================

[1] GET /api/products/999 (404 Not Found) -> Status: 404
    Payload:
{'error': {'code': 'PRODUCT_NOT_FOUND', 'message': 'Product with ID 999 does not exist.', 'details': [{'field': 'product_id', 'message': 'ID 999 not in catalog.'}]}}

[2] POST /api/products (422 Unprocessable Entity) -> Status: 422
    Payload:
{'error': {'code': 'VALIDATION_ERROR', 'message': 'The request payload failed schema validation.', 'details': [{'field': 'body -> name', 'message': 'String should have at least 2 characters'}, {'field': 'body -> price', 'message': 'Input should be greater than 0'}, {'field': 'body -> stock', 'message': 'Input should be a valid integer, unable to parse string as an integer'}]}}

[3] POST /api/users (409 Conflict) -> Status: 409
    Payload:
{'error': {'code': 'USER_ALREADY_EXISTS', 'message': "User account with email 'alex@example.com' already exists.", 'details': [{'field': 'email', 'message': 'Email is registered to another user account.'}]}}

[4] GET /api/crash-me (500 Internal Server Error) -> Status: 500
    Payload:
{'error': {'code': 'INTERNAL_SERVER_ERROR', 'message': 'An unexpected internal server error occurred. Please contact support.', 'details': []}}

======================================================================
Module 04 standardized error handling checks passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Pydantic Error Mapping**: Transforming Pydantic's nested `loc` tuple (e.g. `["body", "items", 0, "quantity"]`) into a string `"body -> items -> 0 -> quantity"` creates a direct, readable locator for frontend client field mapping.
2. **Unhandled Exception Safety**: Verified that when `/api/crash-me` threw a raw `RuntimeError`, the catch-all handler intercepted the crash, output the full stack trace to the server logs, and sent a generic `500 Internal Server Error` response without exposing any internal details.
3. **No Silent 200s**: Every single error condition accurately pairs an appropriate HTTP 4xx/5xx status code with the JSON error body.

### Issues Encountered & Fixes
- **Issue**: Starlette deprecation warnings regarding `HTTP_422_UNPROCESSABLE_ENTITY`.
- **Fix**: Used `status.HTTP_422_UNPROCESSABLE_ENTITY` with standardized JSON response formatting.
