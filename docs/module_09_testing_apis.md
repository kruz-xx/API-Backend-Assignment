# Module 09 — Testing APIs

## Overview
Automated and manual testing strategies for REST APIs: designing comprehensive manual curl test matrices covering happy paths and error boundaries (400/422 validation, 401 unauthorized, 403 forbidden, 404 not found, 409 conflict), understanding the testing pyramid and the trade-offs between unit tests and integration tests, mocking external API dependencies to ensure deterministic CI/CD pipelines, and leveraging pytest fixtures with FastAPI dependency overrides.

---

## Conceptual Questions & Answers

### 1. Manual API Test Suite: Happy Paths and Failure Scenarios
> Write manual tests for your API using `curl` for every endpoint built — happy path AND failure cases.

Comprehensive testing requires validating both the expected successful flow (HTTP 200/201) and all error boundaries:
- `401 Unauthorized`: Missing or invalid Bearer token / API key.
- `403 Forbidden`: Authenticated user lacking admin privileges (RBAC) or attempting to view another user's private resource (BOLA).
- `404 Not Found`: Querying non-existent entity IDs.
- `409 Conflict`: Registering duplicate email addresses.
- `422 Unprocessable Entity`: Request body failing Pydantic schema validation.

---

### 2. Unit Tests vs Integration Tests: The Testing Pyramid
> Explain the difference between unit tests, integration tests, and why both matter.

```text
                  / \
                 /   \           End-to-End (E2E) Tests
                / E2E \          - Fewest in number, tests full multi-step workflows
               /-------\
              / Integr. \        Integration Tests
             /  Tests    \       - Tests Router + Middleware + Pydantic + Service layers
            /-------------\
           /  Unit Tests   \     Unit Tests
          /_________________\    - Pure isolated function tests (e.g. hash_password)
```

| Dimension | Unit Tests | Integration Tests |
| :--- | :--- | :--- |
| **Scope** | A single function or algorithm in isolation | Multiple layers working together (ASGI client, routing, DB) |
| **Dependencies** | All external dependencies mocked | Uses real request lifecycles and schemas |
| **Execution Speed** | Sub-millisecond ($< 1\text{ ms}$) | Fast ($5-50\text{ ms}$) |
| **Failure Pinpointing** | Immediate pinpointing of exact broken line | Verifies end-to-end HTTP contract correctness |

---

### 3. Mocking External API Dependencies
> Explain mocking: why would you mock external calls instead of hitting real third-party APIs during automated test runs?

1. **Determinism & Flakiness Prevention**: External networks experience latency and outages; mocking provides 100% reproducible responses in 0 ms.
2. **Rate Limit & Cost Avoidance**: CI/CD pipelines running hundreds of builds would quickly exhaust third-party API quotas or incur cloud billing fees.
3. **Preventing Test Sandbox Contamination**: Calling real endpoints mutates real external data (sending actual emails or making real financial transactions).
4. **Simulating Edge Cases**: Allows trivial simulation of rare upstream 502/503/504 gateway failures and network timeouts on demand.

---

### 4. Pytest Fixtures and FastAPI Dependency Overrides
> How do pytest fixtures (`conftest.py`) and `app.dependency_overrides` facilitate clean testing?

- **Pytest Fixtures**: Provide modular, reusable setup and teardown logic (e.g. database clearing and reseeding before each test function using `yield`).
- **`app.dependency_overrides`**: Allows test suites to swap out authentication dependencies (`get_current_user`) or database sessions with mock fixtures without editing production code.

---

## Practical: Automated Test Suite & Testing Strategies Implementation

### Implementation
**Files:**
- [`tests/test_module_09_testing_strategies.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_09_testing_strategies.py) (Unit tests, mocking external APIs with `unittest.mock`, and `app.dependency_overrides`)
- [`tests/test_users.py`](file:///c:/office%20files/api-backend-assignment/tests/test_users.py) (User authentication integration tests)
- [`tests/test_products.py`](file:///c:/office%20files/api-backend-assignment/tests/test_products.py) (Catalog CRUD integration tests)
- [`tests/test_orders.py`](file:///c:/office%20files/api-backend-assignment/tests/test_orders.py) (Order transaction & BOLA tests)
- [`tests/test_capstone_e2e.py`](file:///c:/office%20files/api-backend-assignment/tests/test_capstone_e2e.py) (End-to-End complete lifecycle test)

### How I Ran It
```bash
pytest -v
```

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

### Observations / Learnings
1. **Dependency Injection Power**: `app.dependency_overrides` completely decouples tests from database/auth state without requiring monkey-patching or complex subclassing.
2. **Speed & Stability**: Running 50 integration and unit tests took only 0.60 seconds, verifying that test execution is fast enough to run on every commit.
3. **Comprehensive Coverage**: Tests cover happy paths, boundary validations, RBAC permissions, and BOLA attack scenarios.

### Issues Encountered & Fixes
- **Issue**: Pytest attempted to collect test app instance as a test case due to `test_` prefix naming.
- **Fix**: Renamed fixture application variable to `demo_test_app`.
