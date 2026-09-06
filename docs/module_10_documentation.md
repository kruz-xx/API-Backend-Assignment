# Module 10 — API Documentation & OpenAPI Specification

## Overview
Understanding OpenAPI 3.0/3.1 specifications, automated JSON Schema generation, configuring FastAPI metadata (`title`, `version`, `summary`, `tags_metadata`, `description`, `contact`, `license_info`), rich Pydantic field docstrings with realistic payload examples, and interactive documentation via Swagger UI (`/docs`) and ReDoc (`/redoc`).

---

## Conceptual Questions & Answers

### 1. OpenAPI Specification & Swagger UI
> What is the difference between the OpenAPI Specification (OAS) and Swagger UI / ReDoc? How does FastAPI automate schema generation from Pydantic types?

**Answer:**

- **OpenAPI Specification (OAS)**:
  A vendor-neutral, machine-readable specification (standardized JSON/YAML format) describing RESTful APIs. It defines available endpoints, HTTP methods, input parameters, request bodies, response shapes, authentication mechanisms, and data schemas according to the JSON Schema standard.

- **Swagger UI & ReDoc**:
  Interactive frontend web interfaces that consume the raw `/openapi.json` specification to render human-readable, interactive documentation:
  - **Swagger UI (`/docs`)**: Provides an interactive "Try it out" sandbox allowing developers to execute live HTTP requests directly from the browser.
  - **ReDoc (`/redoc`)**: Provides a clean, responsive, multi-column reference view optimized for developer reading and SDK navigation.

- **How FastAPI Automates Schema Generation**:
  1. **Route Reflection**: FastAPI inspects route decorators, HTTP verbs, paths, and status codes.
  2. **Pydantic Type Extraction**: It analyzes Pydantic models, type annotations (`int`, `str`, `EmailStr`), `Field(description=..., examples=...)`, and validation constraints (`gt=0`, `min_length=2`).
  3. **JSON Schema Compilation**: Compiles these types into standard OpenAPI 3.1.0 JSON Schema objects and serves them dynamically at `/openapi.json`.

---

### 2. Best Practices for API Documentation
> Explain best practices for API documentation: documenting response codes (200, 201, 400, 401, 403, 404, 422), field descriptions, deprecation notices, and realistic JSON examples.

**Best Practices:**
1. **Explicit Error Status Codes**: Document all expected failure codes (`400`, `401`, `403`, `404`, `422`, `429`, `500`) with matching schema structures so client SDK generators produce typed error handlers.
2. **Realistic Payload Examples**: Supply representative example payloads using Pydantic's `json_schema_extra={"example": ...}` so developers understand expected formats immediately.
3. **Field-Level Descriptions**: Add clear descriptions explaining business constraints (e.g. "Unit price in USD, strictly positive", "Available warehouse inventory").
4. **Deprecation Notices**: Mark obsolete endpoints or fields with `deprecated=True` to give clients migration warnings before breaking removals.
5. **Tags & Logical Grouping**: Group endpoints by domain feature (`Users`, `Products`, `Orders`, `System`) with descriptive summaries.

---

## Practical: OpenAPI Specification & Documentation Configuration

### Implementation
**File:** [`src/practicals/module_10_docs_demo.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_10_docs_demo.py)  
**Main App:** [`src/main.py`](file:///c:/office%20files/api-backend-assignment/src/main.py)  
**Tests:** [`tests/test_module_10_documentation.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_10_documentation.py)

Implemented:
1. Production OpenAPI 3.1 configuration with application metadata, contact information, license, and `tags_metadata`.
2. Rich Pydantic schemas with field descriptions and realistic JSON examples.
3. Endpoint documentation with summaries, operation descriptions, and response status codes.
4. Programmatic verification of `/openapi.json`, `/docs` (Swagger UI), and `/redoc`.

### How I Ran It
```bash
python -m src.practicals.module_10_docs_demo
```

### Testing
```bash
pytest tests/test_module_10_documentation.py -v
```

### Result
```text
======================================================================
Module 10: API Documentation & OpenAPI Specification Practical Run
======================================================================

[1] GET /openapi.json -> Status: 200
    OpenAPI Version: 3.1.0
    Title: Enterprise E-Commerce API
    Version: 1.0.0
    Total Documented Routes: 2
    Documented Paths: ['/health', '/products']

[2] GET /docs (Swagger UI) -> Status: 200 OK (HTML interface served)

[3] GET /redoc (ReDoc Interface) -> Status: 200 OK (HTML interface served)

======================================================================
Module 10 OpenAPI documentation checks passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Automated Synchronization**: Because documentation is generated directly from Python code and Pydantic types, the OpenAPI schema is always 100% in sync with the running backend implementation.
2. **Standard Compatibility**: FastAPI 0.110+ generates OpenAPI 3.1.0 schemas which are directly compatible with modern API client generators (like openapi-generator and swagger-codegen).
3. **Interactive Testing**: Accessing `http://127.0.0.1:8000/docs` provides an instant graphical sandbox for testing all API endpoints and authentication headers.

### Issues Encountered & Fixes
- **Issue**: Pydantic V2 changed `example` field configuration from `schema_extra` to `json_schema_extra`.
- **Fix**: Updated models to use `Field(..., json_schema_extra={"example": ...})` conforming to Pydantic V2 standards.
