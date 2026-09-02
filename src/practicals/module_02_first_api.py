"""
Module 02: Building Your First API
Implements:
1. Minimal health check endpoint (GET /health)
2. Path parameters vs Query parameters (GET /items/{item_id}, GET /items?category=...)
3. Request body handling with generated UUIDs (POST /items)
4. Serialization & Deserialization demonstrations (json.dumps / json.loads)
5. Pydantic server-side validation (enforcing constraints, automatic 422 responses)
6. Full in-memory CRUD for a Book resource with standard HTTP verbs and status codes (201, 200, 204, 404)
"""

import json
from typing import Dict, List, Optional
import uuid
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# FastAPI Application Definition
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Book Store CRUD & First API Practical",
    version="1.0.0",
    description="Module 02 practical demonstration of routing, parameters, validation, and full in-memory CRUD."
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, description="Book title must not be empty")
    author: str = Field(..., min_length=1, max_length=100, description="Author name must not be empty")
    price: float = Field(..., gt=0.0, description="Price must be strictly positive")
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


class ItemPayload(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(default="general")
    price: float = Field(..., gt=0.0)


# ---------------------------------------------------------------------------
# In-Memory Storage
# ---------------------------------------------------------------------------
books_db: Dict[int, dict] = {}
book_id_counter = 1

sample_items = {
    1: {"id": 1, "name": "Clean Code", "category": "books", "price": 32.50},
    2: {"id": 2, "name": "Design Patterns", "category": "books", "price": 45.00},
    3: {"id": 3, "name": "Mechanical Keyboard", "category": "electronics", "price": 89.99},
}


def reset_state():
    """Resets in-memory storage for clean test runs."""
    global book_id_counter
    books_db.clear()
    book_id_counter = 1


# ---------------------------------------------------------------------------
# 1. Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="Health check probe")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 2. Path vs Query Parameter Endpoints
# ---------------------------------------------------------------------------
@app.get("/items/{item_id}", tags=["Items"])
def get_item_by_path(item_id: int):
    if item_id not in sample_items:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    return sample_items[item_id]


@app.get("/items", tags=["Items"])
def get_items_by_query(
    category: Optional[str] = Query(None, description="Filter category"),
    limit: int = Query(10, ge=1, le=50, description="Pagination limit")
):
    results = list(sample_items.values())
    if category:
        results = [item for item in results if item["category"].lower() == category.lower()]
    return {
        "count": len(results[:limit]),
        "limit": limit,
        "items": results[:limit]
    }


# ---------------------------------------------------------------------------
# 3. Request Body with Generated ID
# ---------------------------------------------------------------------------
@app.post("/items", status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item_with_id(item: ItemPayload):
    generated_id = str(uuid.uuid4())[:8]
    return {
        "id": generated_id,
        "name": item.name,
        "category": item.category,
        "price": item.price
    }


# ---------------------------------------------------------------------------
# 4. Serialization / Deserialization Helper
# ---------------------------------------------------------------------------
def demonstrate_serialization():
    """
    Explicitly demonstrates Python dict -> JSON wire string (json.dumps)
    and JSON wire string -> Python dict (json.loads).
    """
    raw_json_wire = '{"title": "The Pragmatic Programmer", "price": 42.99, "in_stock": true}'
    # Deserialization
    parsed_dict = json.loads(raw_json_wire)
    parsed_dict["tax"] = round(parsed_dict["price"] * 0.08, 2)
    # Serialization
    outgoing_json_str = json.dumps(parsed_dict, indent=2)
    return parsed_dict, outgoing_json_str


# ---------------------------------------------------------------------------
# 5. Full CRUD Endpoints for Books Resource
# ---------------------------------------------------------------------------
@app.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Books"]
)
def create_book(book: BookCreate):
    global book_id_counter
    book_id = book_id_counter
    book_id_counter += 1

    record = book.model_dump()
    record["id"] = book_id
    books_db[book_id] = record
    return record


@app.get(
    "/books",
    response_model=List[BookResponse],
    tags=["Books"]
)
def list_books(author: Optional[str] = None, limit: int = 10):
    results = list(books_db.values())
    if author:
        results = [b for b in results if author.lower() in b["author"].lower()]
    return results[:limit]


@app.get(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["Books"]
)
def get_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    return books_db[book_id]


@app.patch(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["Books"]
)
def update_book(book_id: int, book_update: BookUpdate):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    stored_book = books_db[book_id]
    update_data = book_update.model_dump(exclude_unset=True)
    stored_book.update(update_data)
    books_db[book_id] = stored_book
    return stored_book


@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Books"]
)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    del books_db[book_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_02_demo():
    reset_state()
    client = TestClient(app)

    print("=" * 70)
    print("Module 02: Building Your First API — Practical Run")
    print("=" * 70)

    # 1. Health check
    res = client.get("/health")
    print(f"\n[1] GET /health -> Status: {res.status_code}, Body: {res.json()}")

    # 2. Path param vs Query param
    res_path = client.get("/items/1")
    print(f"\n[2] GET /items/1 (Path Param) -> Status: {res_path.status_code}, Body: {res_path.json()}")

    res_query = client.get("/items?category=books&limit=2")
    print(f"    GET /items?category=books (Query Param) -> Status: {res_query.status_code}, Body: {res_query.json()}")

    # 3. Serialization demo
    p_dict, out_str = demonstrate_serialization()
    print(f"\n[3] Explicit Serialization / Deserialization:")
    print(f"    Parsed Dict: {p_dict}")
    print(f"    Outgoing Serialized JSON:\n{out_str}")

    # 4. Pydantic Validation Error (422)
    res_val_err = client.post("/books", json={"title": "", "author": "Author", "price": -10.0})
    print(f"\n[4] Invalid Book Payload (POST /books) -> Status: {res_val_err.status_code} (Expected 422)")
    print(f"    Validation Errors: {res_val_err.json()['detail']}")

    # 5. Full Book CRUD
    # CREATE (201)
    res_create = client.post("/books", json={"title": "Fluent Python", "author": "Luciano Ramalho", "price": 49.99, "published_year": 2022})
    print(f"\n[5] CRUD Step 1 (POST /books) -> Status: {res_create.status_code}, Body: {res_create.json()}")

    # READ ALL (200)
    res_list = client.get("/books")
    print(f"    CRUD Step 2 (GET /books) -> Status: {res_list.status_code}, Count: {len(res_list.json())}")

    # READ ONE (200)
    res_get_one = client.get("/books/1")
    print(f"    CRUD Step 3 (GET /books/1) -> Status: {res_get_one.status_code}, Title: {res_get_one.json()['title']}")

    # UPDATE (200)
    res_update = client.patch("/books/1", json={"price": 44.99})
    print(f"    CRUD Step 4 (PATCH /books/1) -> Status: {res_update.status_code}, New Price: {res_update.json()['price']}")

    # DELETE (204)
    res_delete = client.delete("/books/1")
    print(f"    CRUD Step 5 (DELETE /books/1) -> Status: {res_delete.status_code} (Empty content: {len(res_delete.content)} bytes)")

    # VERIFY DELETED (404)
    res_verify_del = client.get("/books/1")
    print(f"    CRUD Step 6 (GET /books/1 after delete) -> Status: {res_verify_del.status_code} (Expected 404)")

    print("\n" + "=" * 70)
    print("Module 02 CRUD & validation demonstration passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_02_demo()
