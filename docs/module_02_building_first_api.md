# Module 02 — Building Your First API

## Overview
Setting up a minimal FastAPI application, understanding endpoints, routing, path and query parameters, JSON request bodies, serialization and deserialization mechanisms, Pydantic data validation, HTTP status codes, and implementing complete in-memory CRUD operations.

---

## Conceptual Questions & Implementation Notes

### 1. Minimal Health Check Endpoint
> **Question:**
> Set up a minimal FastAPI (or Flask) app with one `GET /health` endpoint that returns `{"status": "ok"}`. Run it locally and hit it with `curl`.

**Implementation & Explanation:**

A minimal FastAPI application only requires importing `FastAPI`, instantiating the app, and decorating a handler function with `@app.get("/health")`.

```python
from fastapi import FastAPI

# Instantiate FastAPI application
app = FastAPI(
    title="Minimal Health API",
    version="1.0.0",
    description="A minimal FastAPI application with a health check probe."
)

@app.get("/health")
def health_check():
    """
    Basic health check probe returning server status.
    """
    return {"status": "ok"}
```

**Running Locally with Uvicorn:**
```bash
uvicorn main:app --reload --port 8000
```

**Testing with `curl`:**
```bash
curl -i http://127.0.0.1:8000/health
```

**HTTP Response:**
```http
HTTP/1.1 200 OK
date: Thu, 27 Aug 2026 16:51:20 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

---

### 2. Path Parameters vs. Query Parameters
> **Question:**
> Add a `GET /items/{item_id}` endpoint using a **path parameter**. Explain path parameters vs query parameters, then add a `GET /items?category=books&limit=10` endpoint using **query parameters** to demonstrate the difference.

**Implementation:**

```python
from typing import Optional
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Simulated items database
SAMPLE_ITEMS = {
    1: {"id": 1, "name": "Clean Code", "category": "books", "price": 32.50},
    2: {"id": 2, "name": "Design Patterns", "category": "books", "price": 45.00},
    3: {"id": 3, "name": "Mechanical Keyboard", "category": "electronics", "price": 89.99},
}

# 1. Path Parameter: Identifies a specific individual resource
@app.get("/items/{item_id}")
def get_item_by_id(item_id: int):
    if item_id not in SAMPLE_ITEMS:
        raise HTTPException(status_code=404, detail="Item not found")
    return SAMPLE_ITEMS[item_id]

# 2. Query Parameters: Filter, sort, paginate, or modify resource collection
@app.get("/items")
def get_items(category: Optional[str] = None, limit: int = 10):
    results = list(SAMPLE_ITEMS.values())
    
    if category:
        results = [item for item in results if item["category"].lower() == category.lower()]
        
    return {
        "count": len(results[:limit]),
        "limit": limit,
        "items": results[:limit]
    }
```

**Conceptual Comparison:**

| Feature | Path Parameters | Query Parameters |
| :--- | :--- | :--- |
| **Location** | Embedded directly in the URL path (`/items/{item_id}`) | Appended after `?` as key-value pairs (`?category=books&limit=10`) |
| **Primary Purpose** | **Identity**: Locates a specific, individual resource. | **Modifier**: Filters, sorts, searches, or paginates a collection. |
| **Necessity** | **Mandatory**: The route cannot match without it. | **Optional**: Usually has default fallback values. |
| **Example URL** | `http://127.0.0.1:8000/items/1` | `http://127.0.0.1:8000/items?category=books&limit=10` |

**Testing with `curl`:**
```bash
# Path Parameter request
curl http://127.0.0.1:8000/items/1

# Query Parameters request
curl "http://127.0.0.1:8000/items?category=books&limit=10"
```

**Path Parameter request output**

```
{"id": 1, "name": "Clean Code", "category": "books", "price": 32.5}
```

**Query Parameters request output**

```
{
  "count": 2,
  "limit": 10,
  "items": [
    {
      "id": 1,
      "name": "Clean Code",
      "category": "books",
      "price": 32.5
    },
    {
      "id": 2,
      "name": "Design Patterns",
      "category": "books",
      "price": 45.0
    }
  ]
}
```
---

### 3. Request Body vs. Query Parameters
> **Question:**
> Add a `POST /items` endpoint that accepts a JSON **request body** and returns it back with a generated `id`. Explain request body vs query params — when do you use which? (Rule of thumb: body for data being created/sent, query params for filtering/optional modifiers, path params for identifying a specific resource.)

**Implementation:**

```python
import uuid
from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    category: str
    price: float

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    generated_id = str(uuid.uuid4())[:8]
    created_item = {
        "id": generated_id,
        "name": item.name,
        "category": item.category,
        "price": item.price
    }
    return created_item
```

**Conceptual Breakdown & Decision Guide:**

- **Request Body (JSON Payload):**
  - Carries complex, multi-field, structured, nested, or large amounts of data.
  - Placed inside the HTTP message body, keeping the URL clean and avoiding length limits or leaking sensitive data (passwords, PII) into server access logs, browser history, or proxy caches.
  - Used for `POST`, `PUT`, and `PATCH` requests when creating or modifying state.
- **Query Parameters:**
  - Simple key-value pairs in the URL (`?status=active&sort=desc`).
  - Readily bookmarkable, shareable, and cacheable.
  - Used for `GET` requests to filter, sort, search, or paginate without modifying server state.

> **💡 The Rule of Thumb:**
> - **Path Parameters:** Identifying a specific, existing resource (`/users/42`).
> - **Query Parameters:** Filtering, sorting, paginating, or applying optional modifiers (`/users?role=admin&limit=20`).
> - **Request Body:** Data being created, updated, or large complex payloads sent to the server (`POST /users` with `{ "name": "Alice", ... }`).

**Testing with `curl`:**
```bash
curl -X POST "http://127.0.0.1:8000/items" \
     -H "Content-Type: application/json" \
     -d '{"name": "Pragmatic Programmer", "category": "books", "price": 39.99}'
```

**Response:**
```json
{
  "id": "e9a8f12c",
  "name": "Pragmatic Programmer",
  "category": "books",
  "price": 39.99
}
```

---

### 4. Serialization & Deserialization
> **Question:**
> Explain **serialization/deserialization**: your Python dict/object has to become JSON text to travel over the network (serialize), and the JSON the client sends has to become a Python object again on the server (deserialize). Show this happening explicitly with `json.dumps()`/`json.loads()` even though your framework does it automatically.

**Explanation:**

Network protocols (HTTP/TCP) transfer data as raw text streams or byte arrays. They cannot transmit native in-memory runtime objects (such as Python dictionaries, custom class instances, or memory pointers).

- **Serialization (Encoding / Marshaling):** Converting an in-memory runtime object (e.g., Python `dict` or Pydantic model) into a standardized wire format string (like a JSON string) to be transmitted over the network or saved to disk.
- **Deserialization (Decoding / Unmarshaling):** Parsing the received wire format string (raw JSON text) back into a native programming language object (Python `dict`, object) that backend code can interact with.

```text
+---------------------+                            +----------------------+
|     CLIENT APP      |                            |     SERVER APP       |
|                     |  1. Serialize to JSON text |                      |
| Python/JS Object    | -------------------------> | Receives Wire String |
|                     |   (HTTP Request Body)      |                      |
|                     |                            | 2. Deserialize (loads)|
|                     |                            | -> Python Dict       |
|                     |                            |                      |
|                     |                            | 3. Process Logic     |
|                     |                            |                      |
| Receives Wire String| <------------------------- | 4. Serialize (dumps) |
| 5. Deserialize      |   (HTTP Response Body)     | -> JSON String Text  |
| -> Client Object    |  Sends JSON text back      |                      |
+---------------------+                            +----------------------+
```

**Explicit Demonstration with Python's Standard `json` Library:**

```python
import json

# ============================================================================
# 1. DESERIALIZATION: Incoming JSON Wire Text -> Python Dict (json.loads)
# ============================================================================
wire_payload = '{"item_name": "Mechanical Keyboard", "price": 120.50, "in_stock": true}'
print("Wire format type:", type(wire_payload)) # <class 'str'>

# Deserializing raw text into Python data structure
python_dict = json.loads(wire_payload)
print("Deserialized type:", type(python_dict)) # <class 'dict'>
print(f"Parsed Name: {python_dict['item_name']}, Price: ${python_dict['price']}")

# Modify/enrich data in memory
python_dict["tax_amount"] = round(python_dict["price"] * 0.08, 2)
python_dict["total"] = round(python_dict["price"] + python_dict["tax_amount"], 2)

# ============================================================================
# 2. SERIALIZATION: Python Dict -> Outgoing JSON Wire Text (json.dumps)
# ============================================================================
outgoing_json_text = json.dumps(python_dict, indent=2)
print("\nSerialized outgoing payload string:")
print(outgoing_json_text)
print("Outgoing type:", type(outgoing_json_text)) # <class 'str'>
```
Wire format type: <class 'str'>
Deserialized type: <class 'dict'>
Parsed Name: Mechanical Keyboard, Price: $120.5

Serialized outgoing payload string:
{
  "item_name": "Mechanical Keyboard",
  "price": 120.5,
  "in_stock": true,
  "tax_amount": 9.64,
  "total": 130.14
}
Outgoing type: <class 'str'>


*Note: While FastAPI and Pydantic handle serialization and deserialization automatically under the hood via high-performance C/Rust parsers (`pydantic-core`), understanding `loads` (string to object) and `dumps` (object to string) is fundamental to web APIs.*

---

### 5. Pydantic Models & Server-Side Validation
> **Question:**
> If using FastAPI: use **Pydantic models** to validate the request body (e.g., `price` must be a positive float, `name` must be a non-empty string). Show what happens when you send invalid data — the automatic `422` response. Explain why server-side validation is non-negotiable even if the frontend also validates.

**Implementation:**

```python
from fastapi import FastAPI, status
from pydantic import BaseModel, Field

app = FastAPI()

class ValidatedItem(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Name must be a non-empty string"
    )
    price: float = Field(
        ..., 
        gt=0.0, 
        description="Price must be a strictly positive float"
    )
    category: str = Field(
        default="general", 
        min_length=2
    )

@app.post("/items/validated", status_code=status.HTTP_201_CREATED)
def create_validated_item(item: ValidatedItem):
    return {
        "message": "Validation passed",
        "data": item.model_dump()
    }
```

**Testing with Invalid Data (Empty `name` & Negative `price`):**
```bash
curl -X POST http://127.0.0.1:8000/items/validated \
     -H "Content-Type: application/json" \
     -d '{"name": "", "price": -10.50}'
```

**Automatic `422 Unprocessable Entity` Response:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "name"
      ],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    },
    {
      "type": "greater_than",
      "loc": [
        "body",
        "price"
      ],
      "msg": "Input should be greater than 0",
      "input": -10.5,
      "ctx": {
        "gt": 0.0
      }
    }
  ]
}
```

**Why Server-Side Validation is Non-Negotiable:**
1. **Frontend Validation is Bypassed Easily:** Frontend validation is strictly a user-experience (UX) convenience (providing quick visual feedback). Any client can bypass the UI entirely by crafting raw HTTP requests using `curl`, Postman, Python scripts, or DevTools.
2. **Zero-Trust Security Boundary:** The backend is the ultimate guardian of database integrity and business invariants. Malformed inputs could cause application crashes, database corruptions, integer overflow attacks, or SQL/NoSQL injection vulnerabilities.
3. **Multi-Client Consistency:** Real-world APIs often serve web applications, mobile apps (iOS/Android), CLI tools, background workers, and external third-party integrations. Server-side validation guarantees consistent validation across all consumers.

---

### 6. Full In-Memory CRUD for a Resource (Book)
> **Question:**
> Build out full CRUD (Create, Read, Update, Delete) for a single resource (e.g. Book) using an in-memory list/dict as fake storage (no real database needed yet). Use the correct HTTP method and status code for each operation (`POST`->`201`, `GET`->`200`, `PUT`/`PATCH`->`200`, `DELETE`->`204`).

**Complete Implementation:**

```python
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

app = FastAPI(title="Book Resource CRUD API")

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    author: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0.0)
    published_year: Optional[int] = Field(None, ge=1000, le=2100)

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0.0)
    published_year: Optional[int] = Field(None, ge=1000, le=2100)

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    price: float
    published_year: Optional[int] = None

# ---------------------------------------------------------------------------
# In-Memory Storage (Fake DB)
# ---------------------------------------------------------------------------
books_db: dict[int, dict] = {}
id_counter = 1

# ---------------------------------------------------------------------------
# 1. CREATE: POST /books -> 201 Created
# ---------------------------------------------------------------------------
@app.post(
    "/books", 
    response_model=BookResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book"
)
def create_book(book: BookCreate):
    global id_counter
    book_id = id_counter
    id_counter += 1
    
    record = book.model_dump()
    record["id"] = book_id
    books_db[book_id] = record
    return record

# ---------------------------------------------------------------------------
# 2. READ ALL: GET /books -> 200 OK
# ---------------------------------------------------------------------------
@app.get(
    "/books", 
    response_model=List[BookResponse], 
    status_code=status.HTTP_200_OK,
    summary="List all books with optional filtering"
)
def list_books(author: Optional[str] = None, limit: int = 10):
    results = list(books_db.values())
    if author:
        results = [b for b in results if author.lower() in b["author"].lower()]
    return results[:limit]

# ---------------------------------------------------------------------------
# 3. READ ONE: GET /books/{book_id} -> 200 OK (or 404 Not Found)
# ---------------------------------------------------------------------------
@app.get(
    "/books/{book_id}", 
    response_model=BookResponse, 
    status_code=status.HTTP_200_OK,
    summary="Get single book by ID"
)
def get_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with id {book_id} not found"
        )
    return books_db[book_id]

# ---------------------------------------------------------------------------
# 4. UPDATE: PATCH /books/{book_id} -> 200 OK (or 404 Not Found)
# ---------------------------------------------------------------------------
@app.patch(
    "/books/{book_id}", 
    response_model=BookResponse, 
    status_code=status.HTTP_200_OK,
    summary="Partially update a book"
)
def update_book(book_id: int, book_update: BookUpdate):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with id {book_id} not found"
        )
    
    stored_book = books_db[book_id]
    # Extract only fields explicitly provided by the caller
    update_data = book_update.model_dump(exclude_unset=True)
    stored_book.update(update_data)
    books_db[book_id] = stored_book
    return stored_book

# ---------------------------------------------------------------------------
# 5. DELETE: DELETE /books/{book_id} -> 204 No Content (or 404 Not Found)
# ---------------------------------------------------------------------------
@app.delete(
    "/books/{book_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book"
)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book with id {book_id} not found"
        )
    del books_db[book_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```
**Outputs:**

**1. Create a Book (POST -> 201) output**
```
{"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho", "price": 49.99, "published_year": 2022}
```

**2. List all Books (GET -> 200) output**
```
[
  {
    "id": 1,
    "title": "Fluent Python",
    "author": "Luciano Ramalho",
    "price": 49.99,
    "published_year": 2022
  }
]
```

**3. Read specific Book by ID (GET -> 200) output**
```
{"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho", "price": 49.99, "published_year": 2022}
```

**4. Partial update price (PATCH -> 200) output**
```
{"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho", "price": 44.99, "published_year": 2022}
```

**5. Delete the Book (DELETE -> 204) output** (Includes -i for headers)
```
HTTP/1.1 204 No Content
date: Mon, 31 Aug 2026 01:03:00 GMT
server: uvicorn
```

**6. Verify Book is Deleted (GET -> 404) output** (Includes -i for headers)
```
HTTP/1.1 404 Not Found
date: Mon, 31 Aug 2026 01:03:05 GMT
server: uvicorn
content-length: 31
content-type: application/json
```

{"detail":"Book with id 1 not found"}



**CRUD Operation Mapping Table:**

| Operation | HTTP Verb | URI Path | Request Payload | Response Code | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Create** | `POST` | `/books` | JSON Body (`BookCreate`) | `201 Created` | Creates new book resource |
| **Read (All)** | `GET` | `/books` | Query Params (`?author=...&limit=...`) | `200 OK` | Retrieves list of books |
| **Read (One)** | `GET` | `/books/{book_id}` | Path Parameter | `200 OK` | Retrieves specific book by ID |
| **Update** | `PUT` / `PATCH` | `/books/{book_id}` | JSON Body (`BookUpdate`) | `200 OK` | Modifies existing book |
| **Delete** | `DELETE` | `/books/{book_id}` | Path Parameter | `204 No Content` | Removes book resource |

**Step-by-Step `curl` Verification Workflow:**

```bash
# 1. Create a Book (POST -> 201)
curl -X POST http://127.0.0.1:8000/books \
     -H "Content-Type: application/json" \
     -d '{"title": "Fluent Python", "author": "Luciano Ramalho", "price": 49.99, "published_year": 2022}'

# 2. List all Books (GET -> 200)
curl http://127.0.0.1:8000/books

# 3. Read specific Book by ID (GET -> 200)
curl http://127.0.0.1:8000/books/1

# 4. Partial update price (PATCH -> 200)
curl -X PATCH http://127.0.0.1:8000/books/1 \
     -H "Content-Type: application/json" \
     -d '{"price": 44.99}'

# 5. Delete the Book (DELETE -> 204)
curl -i -X DELETE http://127.0.0.1:8000/books/1

# 6. Verify Book is Deleted (GET -> 404)
curl -i http://127.0.0.1:8000/books/1
```

---


