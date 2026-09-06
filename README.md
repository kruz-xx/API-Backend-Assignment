# API Backend Assignment & Practical Implementation

A modular, production-ready backend project implementing comprehensive RESTful API and GraphQL architecture in Python (FastAPI, Pydantic, Strawberry GraphQL, HTTPX, Pytest).

This repository contains both theoretical modules and **real, fully implemented and tested practical source files** covering Modules 00 through 12.

---

## 📁 Repository Structure

```text
├── docs/                           # Theoretical answers and hands-on practical documentation
│   ├── module_00_prerequisites.md
│   ├── module_01_http_basics.md
│   ├── module_02_building_first_api.md
│   ├── module_03_rest_principles.md
│   ├── module_04_errors_and_validation.md
│   ├── module_05_auth_and_security.md
│   ├── module_06_consuming_external_apis.md
│   ├── module_07_rate_limiting_and_caching.md
│   ├── module_08_api_security.md
│   ├── module_09_testing_apis.md
│   ├── module_10_documentation.md
│   ├── module_11_graphql.md
│   └── module_12_capstone.md
│
├── src/                            # Production backend source code
│   ├── config.py                   # Pydantic Settings & environment config
│   ├── main.py                     # FastAPI application gateway & middlewares
│   ├── middlewares/                # Centralized exception handlers
│   │   └── error_handler.py
│   ├── models/                     # Pydantic domain models & schemas
│   │   └── schemas.py
│   ├── practicals/                 # Standalone runnable practical exercise implementations
│   │   ├── module_01_http_client.py
│   │   ├── module_02_first_api.py
│   │   ├── module_03_rest_api.py
│   │   ├── module_04_error_handling.py
│   │   ├── module_05_auth_demo.py
│   │   ├── module_06_external_client.py
│   │   ├── module_07_rate_limit_cache.py
│   │   ├── module_08_security_demo.py
│   │   ├── module_10_docs_demo.py
│   │   └── module_11_graphql_app.py
│   ├── routers/                    # RESTful & GraphQL routers
│   │   ├── graphql_router.py
│   │   ├── orders.py
│   │   ├── products.py
│   │   └── users.py
│   └── services/                   # Authentication & security services
│       └── auth.py
│
├── tests/                          # Automated Pytest suite (50 tests)
│   ├── conftest.py
│   ├── test_capstone_e2e.py
│   ├── test_module_01_http.py
│   ├── test_module_02_first_api.py
│   ├── test_module_03_rest.py
│   ├── test_module_04_errors.py
│   ├── test_module_05_auth.py
│   ├── test_module_06_external_client.py
│   ├── test_module_07_rate_limit_cache.py
│   ├── test_module_08_security.py
│   ├── test_module_09_testing_strategies.py
│   ├── test_module_10_documentation.py
│   ├── test_module_11_graphql.py
│   ├── test_orders.py
│   ├── test_products.py
│   └── test_users.py
│
└── requirements.txt                # Python project dependencies
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Complete Test Suite
```bash
pytest -v
```

### 3. Start the Live Server
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Once started, access:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **GraphQL Playground**: [http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql)
- **OpenAPI 3.1 JSON Specification**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 🛠️ Running Individual Practicals

Each practical module can be executed directly from the terminal to inspect live outputs:

```bash
# Module 01: HTTP Protocol & Methods Inspector
python -m src.practicals.module_01_http_client

# Module 02: In-Memory Book CRUD & Serialization Demo
python -m src.practicals.module_02_first_api

# Module 03: REST Pagination, Filtering & API Versioning (v1 vs v2)
python -m src.practicals.module_03_rest_api

# Module 04: Standardized Error Envelopes & 500 Sanitization
python -m src.practicals.module_04_error_handling

# Module 05: API Keys, JWT Signature Verification & RBAC
python -m src.practicals.module_05_auth_demo

# Module 06: Resilient External Client (Backoff, Retries & 429 Handling)
python -m src.practicals.module_06_external_client

# Module 07: Sliding Window Rate Limiting, ETag Caching & N+1 Benchmark
python -m src.practicals.module_07_rate_limit_cache

# Module 08: Input Validation Security, CORS & BOLA/IDOR Defense
python -m src.practicals.module_08_security_demo

# Module 10: OpenAPI 3.1 Schema & Metadata Inspection
python -m src.practicals.module_10_docs_demo

# Module 11: Strawberry GraphQL Queries & Mutations
python -m src.practicals.module_11_graphql_app
```

---

## 🧪 Testing Summary

- **Total Test Cases**: 50 automated tests passing with 0 failures
- **Coverage**:
  - Unit tests: Hash verification, token decoding, validation algorithms
  - Integration tests: HTTP verbs, headers, status codes, query filtering, pagination, error schemas, rate limits, caching, CORS preflights, RBAC permissions, BOLA checks, and GraphQL field selection
  - End-to-End tests: Complete user lifecycle from registration, login, product catalog administration, customer ordering with inventory deduction, to security protection