# Module 12 — Capstone Project: Production-Ready Mini API

## Overview
Architecting and building a unified, production-ready, modular REST and GraphQL backend incorporating all concepts from Modules 00 through 11: configuration management (`pydantic-settings`), password hashing (`SHA256`/`bcrypt`), JWT token issuance & signature validation, Role-Based Access Control (RBAC), centralized standardized error handling, pagination, query filtering/sorting, inventory reservation, BOLA/IDOR protection, CORS configuration, interactive OpenAPI 3.1 documentation, and Strawberry GraphQL.

---

## 🏗️ Architecture & Component Design

```text
+-----------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION GATEWAY                               |
|                                     (src/main.py)                                       |
+-----------------------------------------------------------------------------------------+
       │                             │                                   │
       ▼                             ▼                                   ▼
 [CORSMiddleware]       [Centralized Error Handlers]            [OpenAPI 3.1 Specs]
 Whitelisted Origins    (AppError, 422, 500 Sanitization)       (/docs, /redoc, /openapi.json)
       │
       ├───────────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
+---------------------+     +---------------------+     +---------------------+
|   Users & Auth      |     |  Products Catalog   |     | Orders Transactions |
| (src/routers/users) |     | (src/routers/prod)  |     | (src/routers/order) |
+---------------------+     +---------------------+     +---------------------+
| - POST /register    |     | - GET /products     |     | - POST /orders      |
| - POST /login       |     |   (filter/paginate) |     |   (stock deduct)    |
| - GET /me           |     | - GET /products/{id}|     | - GET /orders       |
| - GET / (Admin RBAC)|     | - POST / (Admin)    |     | - GET /orders/{id}  |
+---------------------+     | - PATCH / (Admin)   |     |   (BOLA Protected)  |
                            | - DELETE / (Admin)  |     +---------------------+
                            +---------------------+                │
                                       │                           │
                                       ├───────────────────────────┘
                                       ▼
                            +---------------------+
                            |   GraphQL Router    |
                            | (/graphql Strawberry)|
                            +---------------------+
                            | - Query: products   |
                            | - Query: orders     |
                            | - Mut: createProduct|
                            +---------------------+
```

---

## 🚀 Practical: Unified Capstone API & E2E Verification

### Implementation Files
- **Application Entrypoint:** [`src/main.py`](file:///c:/office%20files/api-backend-assignment/src/main.py)
- **Configuration:** [`src/config.py`](file:///c:/office%20files/api-backend-assignment/src/config.py)
- **Data Models & Schemas:** [`src/models/schemas.py`](file:///c:/office%20files/api-backend-assignment/src/models/schemas.py)
- **Authentication & RBAC:** [`src/services/auth.py`](file:///c:/office%20files/api-backend-assignment/src/services/auth.py)
- **Exception Middlewares:** [`src/middlewares/error_handler.py`](file:///c:/office%20files/api-backend-assignment/src/middlewares/error_handler.py)
- **Routers:**
  - [`src/routers/users.py`](file:///c:/office%20files/api-backend-assignment/src/routers/users.py)
  - [`src/routers/products.py`](file:///c:/office%20files/api-backend-assignment/src/routers/products.py)
  - [`src/routers/orders.py`](file:///c:/office%20files/api-backend-assignment/src/routers/orders.py)
  - [`src/routers/graphql_router.py`](file:///c:/office%20files/api-backend-assignment/src/routers/graphql_router.py)
- **Full Test Suite:** [`tests/test_capstone_e2e.py`](file:///c:/office%20files/api-backend-assignment/tests/test_capstone_e2e.py)

---

### How I Ran It

1. **Start the Live ASGI Server:**
   ```bash
   uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Execute Full Automated Test Suite:**
   ```bash
   pytest -v
   ```

---

### Testing Workflow & Scenarios

The comprehensive end-to-end test suite validates the entire business lifecycle:

1. **Health Check Probe (`GET /health`)**: Verifies operational readiness (`200 OK`).
2. **User Registration (`POST /api/v1/users/register`)**: Registers an Administrator account and two distinct Customer accounts (`201 Created`).
3. **Authentication (`POST /api/v1/users/login`)**: Verifies passwords, computes cryptographic JWT signatures, and returns Bearer tokens.
4. **Product Creation (`POST /api/v1/products`)**: Administrator creates new catalog items with price, inventory stock, and categorization (`201 Created`).
5. **RBAC Authorization Enforcement**: Customer attempts to create product and is rejected with `403 Forbidden`.
6. **Catalog Discovery (`GET /api/v1/products?category=audio`)**: Customers filter catalog items by category and price bounds.
7. **Order Transaction (`POST /api/v1/orders`)**: Customer purchases multiple items; server computes line-item subtotals, verifies available warehouse stock, and deducts inventory atomically.
8. **Inventory Guard (`POST /api/v1/orders`)**: Customer attempts to order more units than available in stock; rejected with `400 Bad Request (INSUFFICIENT_STOCK)`.
9. **Resource Retrieval (`GET /api/v1/orders/{id}`)**: Customer retrieves their order receipt (`200 OK`).
10. **OWASP BOLA Protection (`GET /api/v1/orders/{id}`)**: Another customer attempts to view the private order receipt; rejected with `403 Forbidden (FORBIDDEN_RESOURCE)`.
11. **GraphQL Execution (`POST /graphql`)**: Executes exact field selection queries and mutations via the Strawberry GraphQL router.

---

### Result

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\office files\api-backend-assignment
plugins: anyio-4.14.2
collected 50 items

tests/test_capstone_e2e.py::test_capstone_full_ecommerce_lifecycle PASSED [  2%]
tests/test_module_01_http.py::test_module_01_http_verbs_and_headers PASSED [  4%]
tests/test_module_01_http.py::test_module_01_script_execution PASSED     [  6%]
tests/test_module_02_first_api.py::test_module_02_health_and_parameters PASSED [  8%]
tests/test_module_02_first_api.py::test_module_02_serialization_logic PASSED [ 10%]
tests/test_module_02_first_api.py::test_module_02_pydantic_validation_and_crud PASSED [ 12%]
tests/test_module_03_rest.py::test_module_03_pagination PASSED           [ 14%]
tests/test_module_03_rest.py::test_module_03_filtering_sorting_searching PASSED [ 16%]
tests/test_module_03_rest.py::test_module_03_api_versioning_schemas PASSED [ 18%]
tests/test_module_04_errors.py::test_module_04_error_shapes PASSED       [ 20%]
tests/test_module_05_auth.py::test_module_05_api_key_auth PASSED         [ 22%]
tests/test_module_05_auth.py::test_module_05_jwt_login_and_tampering PASSED [ 24%]
tests/test_module_05_auth.py::test_module_05_rbac_enforcement PASSED     [ 26%]
tests/test_module_06_external_client.py::test_module_06_resilient_client_success PASSED [ 28%]
tests/test_module_06_external_client.py::test_module_06_retry_backoff_and_recovery PASSED [ 30%]
tests/test_module_06_external_client.py::test_module_06_non_retryable_failure_abort PASSED [ 32%]
tests/test_module_06_external_client.py::test_module_06_rate_limit_retry_after PASSED [ 34%]
tests/test_module_07_rate_limit_cache.py::test_module_07_sliding_window_rate_limiting PASSED [ 36%]
tests/test_module_07_rate_limit_cache.py::test_module_07_etag_conditional_caching PASSED [ 38%]
tests/test_module_07_rate_limit_cache.py::test_module_07_n_plus_one_benchmark_counts PASSED [ 40%]
tests/test_module_08_security.py::test_module_08_negative_quantity_protection PASSED [ 42%]
tests/test_module_08_security.py::test_module_08_cors_preflight PASSED   [ 44%]
tests/test_module_08_security.py::test_module_08_scoped_tokens PASSED    [ 46%]
tests/test_module_08_security.py::test_module_08_bola_idor_protection PASSED [ 48%]
tests/test_module_09_testing_strategies.py::test_unit_password_hashing PASSED [ 50%]
tests/test_module_09_testing_strategies.py::test_dependency_override_bypassing_auth PASSED [ 52%]
tests/test_module_09_testing_strategies.py::test_mocking_external_api_call PASSED [ 54%]
tests/test_module_10_documentation.py::test_module_10_openapi_schema_generation PASSED [ 56%]
tests/test_module_10_documentation.py::test_module_10_main_app_documentation PASSED [ 58%]
tests/test_module_10_documentation.py::test_module_10_runner_script PASSED [ 60%]
tests/test_module_11_graphql.py::test_module_11_graphql_field_selection PASSED [ 62%]
tests/test_module_11_graphql.py::test_module_11_graphql_mutations PASSED [ 64%]
tests/test_module_11_graphql.py::test_module_11_main_app_graphql_route PASSED [ 66%]
tests/test_orders.py::test_create_order_success PASSED                   [ 68%]
tests/test_orders.py::test_create_order_insufficient_stock PASSED        [ 70%]
tests/test_orders.py::test_list_user_orders PASSED                       [ 72%]
tests/test_orders.py::test_order_bola_protection PASSED                  [ 74%]
tests/test_products.py::test_list_products PASSED                        [ 76%]
tests/test_products.py::test_filter_products_by_category PASSED          [ 78%]
tests/test_products.py::test_get_product_by_id PASSED                    [ 80%]
tests/test_products.py::test_get_product_not_found PASSED                [ 82%]
tests/test_products.py::test_create_product_admin PASSED                 [ 84%]
tests/test_products.py::test_create_product_forbidden_for_customer PASSED [ 86%]
tests/test_users.py::test_health_check PASSED                            [ 88%]
tests/test_users.py::test_user_registration_success PASSED               [ 90%]
tests/test_users.py::test_user_registration_duplicate_email PASSED       [ 92%]
tests/test_users.py::test_user_login_success PASSED                      [ 94%]
tests/test_users.py::test_user_login_invalid_password PASSED             [ 96%]
tests/test_users.py::test_get_current_user_profile PASSED                [ 98%]
tests/test_users.py::test_get_current_user_unauthorized PASSED           [100%]

======================= 50 passed in 0.60s ========================
```

---

### Key Observations & Learnings
1. **Unified Request Pipeline**: Integrating authentication dependencies, centralized exception handlers, input schema validation, and database state into a modular FastAPI application provides a clean separation of concerns and maintainability.
2. **Defensive Security at Every Layer**:
   - Pydantic models defend against malformed payloads and negative values.
   - RBAC dependencies defend against unauthorized administrative actions.
   - BOLA checks defend against unauthorized cross-tenant data access.
   - Catch-all exception handlers defend against internal diagnostics and traceback disclosures.
3. **Dual REST & GraphQL Architecture**: Housing RESTful endpoints (`/api/v1/*`) alongside GraphQL (`/graphql`) allows API consumers to choose between standardized HTTP-cached REST operations and flexible field-selection GraphQL queries based on their specific client requirements.
