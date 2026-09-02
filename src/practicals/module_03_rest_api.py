"""
Module 03: REST Principles, Done Properly
Implements:
1. RESTful pagination with metadata envelope (total_count, page, page_size, total_pages, has_next, has_prev, next_page, prev_page)
2. Advanced Query Parameters: Category filtering, keyword searching, and dynamic field sorting (e.g., sort=-price)
3. API Versioning: URL versioning comparing /api/v1/items (flat schema) vs /api/v2/items (nested pricing & availability object)
"""

import math
from typing import Generic, List, Optional, TypeVar
from fastapi import APIRouter, FastAPI, HTTPException, Query, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Schemas & Models
# ---------------------------------------------------------------------------
class PaginationMetadata(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMetadata


class CatalogItem(BaseModel):
    id: int
    name: str
    price: float
    category: str


# Version 1 Schema: Flat structure
class ItemResponseV1(BaseModel):
    id: int
    name: str
    price: float


# Version 2 Schema: Restructured with nested pricing metadata and stock flag
class PriceDetailV2(BaseModel):
    amount: float
    currency: str
    formatted: str


class ItemResponseV2(BaseModel):
    id: int
    title: str = Field(..., description="Renamed from 'name' to 'title' in V2")
    pricing: PriceDetailV2
    in_stock: bool


# ---------------------------------------------------------------------------
# Sample Dataset
# ---------------------------------------------------------------------------
SAMPLE_CATALOG = [
    {"id": 1, "name": "Harry Potter and the Chamber of Secrets", "category": "books", "price": 26.99, "currency": "USD", "stock": 15},
    {"id": 2, "name": "Harry Potter and the Goblet of Fire", "category": "books", "price": 29.99, "currency": "USD", "stock": 8},
    {"id": 3, "name": "Clean Code", "category": "books", "price": 37.50, "currency": "USD", "stock": 0},
    {"id": 4, "name": "Mechanical Keyboard", "category": "electronics", "price": 89.99, "currency": "USD", "stock": 25},
    {"id": 5, "name": "Wireless Ergonomic Mouse", "category": "electronics", "price": 49.99, "currency": "USD", "stock": 40},
    {"id": 6, "name": "USB-C Multiport Adapter", "category": "electronics", "price": 34.99, "currency": "USD", "stock": 0},
    {"id": 7, "name": "Designing Data-Intensive Applications", "category": "books", "price": 48.00, "currency": "USD", "stock": 12},
    {"id": 8, "name": "The Pragmatic Programmer", "category": "books", "price": 42.50, "currency": "USD", "stock": 5},
]

# ---------------------------------------------------------------------------
# FastAPI App & Routers
# ---------------------------------------------------------------------------
app = FastAPI(
    title="REST Principles & Versioning Demo",
    version="2.0.0"
)

# ---------------------------------------------------------------------------
# 1. Advanced Paginated & Filtered Route (/api/items)
# ---------------------------------------------------------------------------
items_router = APIRouter(prefix="/api/items", tags=["Catalog"])


@items_router.get("", response_model=PaginatedResponse[CatalogItem])
def list_items_paginated(
    category: Optional[str] = Query(None, description="Filter by category (e.g. books, electronics)"),
    search: Optional[str] = Query(None, description="Keyword search in item name"),
    sort: Optional[str] = Query("id", description="Sort field. Prefix '-' for descending order (e.g., '-price')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(4, ge=1, le=50, description="Items per page")
):
    results = list(SAMPLE_CATALOG)

    # 1. Filtering by category
    if category:
        results = [i for i in results if i["category"].lower() == category.lower()]

    # 2. Searching by keyword
    if search:
        kw = search.strip().lower()
        results = [i for i in results if kw in i["name"].lower()]

    # 3. Sorting
    reverse_sort = False
    sort_field = sort
    if sort.startswith("-"):
        reverse_sort = True
        sort_field = sort[1:]

    valid_fields = {"id", "name", "price", "category"}
    if sort_field in valid_fields:
        results.sort(key=lambda x: x[sort_field], reverse=reverse_sort)

    # 4. Pagination calculation
    total_count = len(results)
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    if page > total_pages and total_count > 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page} exceeds total available pages ({total_pages})."
        )

    start_idx = (page - 1) * page_size
    paginated_items = results[start_idx : start_idx + page_size]

    return PaginatedResponse(
        items=[CatalogItem(**item) for item in paginated_items],
        pagination=PaginationMetadata(
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None
        )
    )


# ---------------------------------------------------------------------------
# 2. Version 1 Router (/api/v1/items)
# ---------------------------------------------------------------------------
v1_router = APIRouter(prefix="/api/v1/items", tags=["API Version 1"])


@v1_router.get("", response_model=List[ItemResponseV1])
def get_items_v1():
    return [
        ItemResponseV1(id=item["id"], name=item["name"], price=item["price"])
        for item in SAMPLE_CATALOG
    ]


# ---------------------------------------------------------------------------
# 3. Version 2 Router (/api/v2/items)
# ---------------------------------------------------------------------------
v2_router = APIRouter(prefix="/api/v2/items", tags=["API Version 2"])


@v2_router.get("", response_model=List[ItemResponseV2])
def get_items_v2():
    return [
        ItemResponseV2(
            id=item["id"],
            title=item["name"],
            pricing=PriceDetailV2(
                amount=item["price"],
                currency=item.get("currency", "USD"),
                formatted=f"${item['price']:.2f}"
            ),
            in_stock=item["stock"] > 0
        )
        for item in SAMPLE_CATALOG
    ]


app.include_router(items_router)
app.include_router(v1_router)
app.include_router(v2_router)


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_03_demo():
    client = TestClient(app)

    print("=" * 70)
    print("Module 03: REST Principles, Pagination & Versioning Practical Run")
    print("=" * 70)

    # 1. Pagination Test
    res_page = client.get("/api/items?page=1&page_size=3")
    print(f"\n[1] GET /api/items?page=1&page_size=3 -> Status: {res_page.status_code}")
    print(f"    Total Count: {res_page.json()['pagination']['total_count']}, Has Next: {res_page.json()['pagination']['has_next']}")
    print(f"    Page 1 Item Count: {len(res_page.json()['items'])}")

    # 2. Filtering + Searching + Sorting Test
    res_filter = client.get("/api/items?category=books&search=harry&sort=-price")
    print(f"\n[2] GET /api/items?category=books&search=harry&sort=-price -> Status: {res_filter.status_code}")
    print(f"    Returned Items: {[i['name'] + ' ($' + str(i['price']) + ')' for i in res_filter.json()['items']]}")

    # 3. Versioning V1 vs V2
    res_v1 = client.get("/api/v1/items")
    print(f"\n[3] V1 Response Schema (GET /api/v1/items):")
    print(f"    Sample V1 Item: {res_v1.json()[0]}")

    res_v2 = client.get("/api/v2/items")
    print(f"\n[4] V2 Response Schema (GET /api/v2/items):")
    print(f"    Sample V2 Item: {res_v2.json()[0]}")

    print("\n" + "=" * 70)
    print("Module 03 REST pagination & versioning checks passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_03_demo()
