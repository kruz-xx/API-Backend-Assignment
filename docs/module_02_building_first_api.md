# Module 02 — Building Your First API

## Overview
Setting up a minimal FastAPI application, understanding endpoints, routing, path and query parameters, JSON request bodies, serialization and deserialization mechanisms, Pydantic data validation, HTTP status codes, and implementing complete in-memory CRUD operations.

---

## Conceptual Questions & Answers

### 1. Minimal Health Check Endpoint
> Set up a minimal FastAPI (or Flask) app with one `GET /health` endpoint that returns `{"status": "ok"}`. Run it locally and hit it with `curl`.

**Explanation:**
A minimal FastAPI application instantiates the `FastAPI` class and defines route decorators such as `@app.get("/health")`. When invoked, FastAPI automatically serializes the returned Python dictionary into an HTTP response with `Content-Type: application/json` and status code `200 OK`.

---

### 2. Path Parameters vs. Query Parameters
> Explain path parameters vs query parameters, then demonstrate the difference with `/items/{item_id}` vs `/items?category=books&limit=10`.

**Comparison:**

| Feature | Path Parameters | Query Parameters |
| :--- | :--- | :--- |
| **Location** | Embedded in URL path (`/items/{item_id}`) | Appended after `?` as key-value pairs (`?category=books&limit=10`) |
| **Primary Purpose** | **Identity**: Locates a specific, individual resource. | **Modifier**: Filters, sorts, searches, or paginates a collection. |
| **Necessity** | **Mandatory**: Route will not match without it. | **Optional**: Usually has default fallback values. |
| **Example** | `GET /items/42` | `GET /items?category=books&limit=10` |

---

### 3. Request Body vs. Query Parameters
> Explain request body vs query params — when do you use which?

**Rule of Thumb:**
- **Path Parameters**: Identifying a specific resource (`/users/42`).
- **Query Parameters**: Filtering, sorting, paginating, or applying optional search modifiers (`/users?role=admin&limit=20`).
- **Request Body (JSON)**: Data being created, updated, or large structured payloads sent in `POST`, `PUT`, `PATCH` requests (`POST /users` with `{ "name": "Alice", ... }`). Keeps sensitive fields out of URLs and server access logs.

---

### 4. Serialization & Deserialization
> Explain serialization/deserialization: Python dict/object to JSON text over the network (serialize), and JSON wire text to Python object (deserialize). Show this with `json.dumps()` / `json.loads()`.

**Explanation:**
- **Deserialization (`json.loads`)**: Parsing incoming raw JSON wire text strings into native Python dictionaries/objects.
- **Serialization (`json.dumps`)**: Converting in-memory Python dictionaries/objects into JSON-formatted text strings for network transmission.

---

### 5. Pydantic Models & Server-Side Validation
> Use Pydantic models to validate request bodies. Show what happens when invalid data is sent (automatic 422 response) and explain why server-side validation is non-negotiable.

**Why Server-Side Validation is Non-Negotiable:**
1. **Frontend Validation is Easily Bypassed**: Any HTTP client (`curl`, Postman, automated scripts) can send requests directly to the API without rendering the UI.
2. **Zero-Trust Boundary**: Server-side validation protects database integrity against corruptions, invalid data types, negative numbers, and injection attacks.
3. **Multi-Client Consistency**: Guarantees identical validation rules across web apps, mobile apps, and third-party integrations.

---

## Practical: First API & Full Book CRUD Implementation

### Implementation
**File:** [`src/practicals/module_02_first_api.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_02_first_api.py)  
**Tests:** [`tests/test_module_02_first_api.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_02_first_api.py)

Implemented:
1. `GET /health` endpoint returning `{"status": "ok"}`.
2. Path parameter endpoint (`GET /items/{item_id}`) and query parameter filtering (`GET /items?category=...&limit=...`).
3. Request body handling with UUID generation (`POST /items`).
4. Explicit serialization and deserialization demo with `json.loads()` and `json.dumps()`.
5. Pydantic request validation enforcing non-empty title/author and strictly positive price constraints.
6. Complete in-memory Book CRUD API:
   - `POST /books` -> `201 Created`
   - `GET /books` -> `200 OK`
   - `GET /books/{id}` -> `200 OK` / `404 Not Found`
   - `PATCH /books/{id}` -> `200 OK` / `404 Not Found`
   - `DELETE /books/{id}` -> `204 No Content` / `404 Not Found`

### How I Ran It
```bash
python -m src.practicals.module_02_first_api
```

### Testing
```bash
pytest tests/test_module_02_first_api.py -v
```

### Result
```text
======================================================================
Module 02: Building Your First API — Practical Run
======================================================================

[1] GET /health -> Status: 200, Body: {'status': 'ok'}

[2] GET /items/1 (Path Param) -> Status: 200, Body: {'id': 1, 'name': 'Clean Code', 'category': 'books', 'price': 32.5}
    GET /items?category=books (Query Param) -> Status: 200, Body: {'count': 2, 'limit': 2, 'items': [{'id': 1, 'name': 'Clean Code', 'category': 'books', 'price': 32.5}, {'id': 2, 'name': 'Design Patterns', 'category': 'books', 'price': 45.0}]}

[3] Explicit Serialization / Deserialization:
    Parsed Dict: {'title': 'The Pragmatic Programmer', 'price': 42.99, 'in_stock': True, 'tax': 3.44}
    Outgoing Serialized JSON:
{
  "title": "The Pragmatic Programmer",
  "price": 42.99,
  "in_stock": true,
  "tax": 3.44
}

[4] Invalid Book Payload (POST /books) -> Status: 422 (Expected 422)
    Validation Errors: [{'type': 'string_too_short', 'loc': ['body', 'title'], 'msg': 'String should have at least 1 character', 'input': '', 'ctx': {'min_length': 1}}, {'type': 'greater_than', 'loc': ['body', 'price'], 'msg': 'Input should be greater than 0', 'input': -10.0, 'ctx': {'gt': 0.0}}]

[5] CRUD Step 1 (POST /books) -> Status: 201, Body: {'id': 1, 'title': 'Fluent Python', 'author': 'Luciano Ramalho', 'price': 49.99, 'published_year': 2022}
    CRUD Step 2 (GET /books) -> Status: 200, Count: 1
    CRUD Step 3 (GET /books/1) -> Status: 200, Title: Fluent Python
    CRUD Step 4 (PATCH /books/1) -> Status: 200, New Price: 44.99
    CRUD Step 5 (DELETE /books/1) -> Status: 204 (Empty content: 0 bytes)
    CRUD Step 6 (GET /books/1 after delete) -> Status: 404 (Expected 404)

======================================================================
Module 02 CRUD & validation demonstration passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Pydantic `exclude_unset=True`**: When handling partial updates in `PATCH`, `model.model_dump(exclude_unset=True)` extracts only fields explicitly supplied by the caller, preventing defaults from overwriting unmentioned fields.
2. **Standard Status Codes**: Verified that `POST` returns `201 Created` with the newly assigned ID, while `DELETE` returns `204 No Content` with an empty response body.
3. **Automatic 422 Schemas**: Pydantic intercepts invalid data types and constraint violations before the route handler function runs.

### Issues Encountered & Fixes
- **Issue**: Distinguishing between partial updates (`PATCH`) and full replacement (`PUT`).
- **Fix**: Implemented `BookUpdate` with optional fields and used `exclude_unset=True` to apply selective dictionary updates.
