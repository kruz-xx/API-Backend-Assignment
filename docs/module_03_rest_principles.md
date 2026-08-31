# Module 03 — REST Principles, Done Properly

## Overview
Understanding REST (Representational State Transfer) architecture, Fielding constraints, resource naming conventions, nested sub-resources, pagination strategies, filtering/sorting/searching via query parameters, and API versioning approaches.

---

## Conceptual Questions & Implementation Notes

### 1. The Core Constraints of REST
> Explain what "REST" actually stands for and what the core constraints are (client-server, stateless, cacheable, uniform interface, layered system). You don't need to memorize the Fielding dissertation — just understand the spirit.

**Answer:**
REST stands for **Representational State Transfer**, which is an architectural style defined by **Roy Fielding** in year 2000.

- Resource: Any conceptual entity like User, product oor order can be identified byh a unique URL.
- Representation: The format in which the resource data is transferred. (e.g.: JSON, XML)
- State Transfer: The client interacts with the server by sending a request and receiving a response. The response contains the state of the resource; using standard HTTP verbs like GET, POST, PUT, PATCH or DELETE.

```text
 ┌──────────────┐          Stateless HTTP Request (JSON)          ┌──────────────┐
 │    Client    │ ──────────────────────────────────────────────> │ Load Balancer│
 │(Web / Mobile)│ <────────────────────────────────────────────── │ / Gateway    │
 └──────────────┘          Cacheable Response + Headers           └──────┬───────┘
                                                                         │
                                                          Layered System │
                                                                         ▼
                                                                  ┌──────────────┐
                                                                  │ Server (API) │
                                                                  └──────────────┘
```


The **6 constraints of REST** are:
1. **Client-Server:** The client and server are independent of each other.
2. **Stateless:** The server does not store any information about the client.
3. **Cacheable:** The response from the server can be cached.
4. **Uniform Interface:** The server provides a uniform interface to the client.
5. **Layered System:** The server can be composed of multiple layers.
6. **Code on Demand:** The server can provide code to the client.

---

### 2. REST Resource Naming Conventions & Anti-Patterns
> Explain proper REST resource naming conventions: nouns not verbs (`/users` not `/getUsers`), plural collections, nesting for relationships (`/users/5/orders`). Rewrite 5 badly-named endpoints (`/getAllUsers`, `/user-delete/5`, etc.) into proper REST style.

**Answer:**

A. **Nouns, not Verbs**: URIs identify resources, while HTTP methods specify the action.
   E.g. `/users` instead of `/getAllUsers`.

B. **Plural Collections**: Resources should be named as plural nouns.
   E.g. `/users` instead of `/user`.

C. **Nesting for Relationships**: Nest resources to show relationships.
   E.g. `/users/5/orders` instead of `/users/5/getOrders`.

D. **Use HTTP verbs for actions**: GET, POST, PUT, PATCH, DELETE.
   E.g. `GET /users` instead of `/getUsers`.

E. **Use query parameters for filtering, sorting, searching**: rather than custom path segments
   E.g. `/users?role=admin&sort=desc` instead of `/users?getUsers?role=admin&sort=desc`.



#### Badly-Named Endpoints vs Proper REST Style:
| # | Bad / RPC-Style Endpoint | Proper REST Endpoint | HTTP Verb | Explanation |
| :- | :--- | :--- | :--- | :--- |
| 1 | `GET /getAllUsers` | `/users` | `GET` | Uses GET on the plural collection noun 'users' |
| 2 | `POST /user-delete/5` | `/users/{id}` | `DELETE` | Uses DELETE on the plural collection noun 'users' with the id as a path parameter. |
| 3 | `POST /createUser` | `/users` | `POST` | Uses POST on the plural collection noun 'users' to create a new resource. |
| 4 | `GET /getUserOrders?userId=5` | `/users/{id}/orders` | `GET` | Nested resource 'orders' under 'users' with the id as a path parameter |
| 5 | `POST /updateProductPrice/42` | `/products/{id}` | `PUT`/`PATCH` | Uses PUT/PATCH on the plural collection noun 'products' with the id as a path parameter. |

---

### 3. Pagination & Unbounded Endpoints
> Explain pagination and why you'd never return "all 2 million rows" from a `GET /users` endpoint. Implement `GET /items?page=2&page_size=20` (or cursor-based pagination) on your CRUD API from Module 2, and return metadata (`total_count`, `next_page`) alongside the results.

**Answer & Implementation:**

*Why You Never Return "All 2 Million Rows"*

- **Memory Exhaustion (OOM)**: Loading 2M records into memory causes huge heap allocation spikes and crashes the backend process.
- **Database Saturation**: Full table scans lock tables/pages, block connection pools, and max out disk I/O.
- **Network Bandwidth & Latency**: Serializing and transmitting 100MB+ JSON payloads causes multi-second latencies and mobile client timeouts.
- **Client Freezing**: Mobile apps and browsers freeze when attempting to parse and render tens of thousands of DOM objects.

*Offset vs Cursor Pagination*
Offset/Limit (?page=2&page_size=20): Simple, supports jumping to arbitrary pages. Slower on large offsets (OFFSET 1,000,000), and prone to duplicate items if rows are inserted while paginating.
Cursor/Keyset (?cursor=xyz&limit=20): Constant $O(1)$ fast indexed query, immune to data drift, ideal for infinite feeds, but cannot jump to arbitrary page numbers.

**FastAPI Implementation (GET /items?page=2&page_size=20)**

```python

import math
from typing import Generic, List, Optional, TypeVar
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

T = TypeVar("T")

# Pagination Envelope Schema
class PaginationMetadata(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int]
    prev_page: Optional[int]

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMetadata

class ItemSchema(BaseModel):
    id: int
    name: str
    price: float
    category: str

# In-memory sample database of 100 items
ITEMS_DB = [
    {"id": i, "name": f"Item {i}", "price": round(10.0 + i * 1.5, 2), "category": "books" if i % 2 == 0 else "electronics"}
    for i in range(1, 101)
]

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("", response_model=PaginatedResponse[ItemSchema])
def get_items(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    total_count = len(ITEMS_DB)
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    if page > total_pages and total_count > 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page} exceeds total available pages ({total_pages})."
        )

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = ITEMS_DB[start_idx:end_idx]

    return PaginatedResponse(
        items=[ItemSchema(**item) for item in paginated_items],
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
```
**Sample Output (GET /items?page=2&page_size=20):**
```json
{
  "items": [
    { "id": 21, "name": "Item 21", "price": 41.5, "category": "electronics" }
  ],
  "pagination": {
    "total_count": 100,
    "page": 2,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_prev": true,
    "next_page": 3,
    "prev_page": 1
  }
}

```
---

### 4. Filtering, Sorting, and Searching via Query Parameters
> Explain filtering, sorting, and searching via query params: `GET /items?category=books&sort=-price&search=harry`. Implement at least filtering and sorting on your endpoint.

**Answer & Implementation:**

Query Parameter Mechanics:

- Filtering: Limits records to matching attributes.
E.g. - category=books filters books.

- Sorting: Orders the response by a specific field.
E.g. - sort=-price (sorts order descending by price)

- Searching: Filters records based on a search query.
E.g. - search=harry (searches for 'harry' in the response)


**FastAPI Implementation (GET /items?category=books&sort=-price&search=harry)**


```python
from typing import Optional
from fastapi import APIRouter, Query

CATALOG_DB = [
    {"id": 1, "name": "Harry Potter and the Chamber of Secrets", "category": "books", "price": 26.99},
    {"id": 2, "name": "Harry Potter and the Goblet of Fire", "category": "books", "price": 29.99},
    {"id": 3, "name": "Clean Code", "category": "books", "price": 37.50},
    {"id": 4, "name": "Wireless Mouse", "category": "electronics", "price": 49.99},
]

router = APIRouter(prefix="/items", tags=["Catalog"])

@router.get("")
def list_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keyword in item name"),
    sort: Optional[str] = Query("id", description="Sort field, prefix '-' for descending (e.g., '-price')"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    results = list(CATALOG_DB)

    # 1. Filtering
    if category:
        results = [item for item in results if item["category"].lower() == category.lower()]

    # 2. Searching
    if search:
        query = search.strip().lower()
        results = [item for item in results if query in item["name"].lower()]

    # 3. Sorting
    reverse_sort = False
    sort_field = sort
    if sort.startswith("-"):
        reverse_sort = True
        sort_field = sort[1:]

    valid_fields = {"id", "name", "price", "category"}
    if sort_field in valid_fields:
        results.sort(key=lambda x: x[sort_field], reverse=reverse_sort)

    # 4. Pagination
    total_count = len(results)
    start_idx = (page - 1) * page_size
    paginated_items = results[start_idx : start_idx + page_size]

    return {
        "items": paginated_items,
        "metadata": {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "applied_filters": {
                "category": category,
                "search": search,
                "sort": sort
            }
        }
    }


```

**Output:**

``` json
 {
    "items": [ { "id": 1, "name": "Harry Potter and the Chamber of Secrets", "category": "books", "price": 26.99 }, { "id": 2, "name": "Harry Potter and the Goblet of Fire", "category": "books", "price": 29.99 } ],
    "metadata": {
        "total_count": 2,
        "page": 1,
        "page_size": 10,
        "applied_filters": {
            "category": "books",
            "search": "harry",
            "sort": "-price"
        }
    }
}
```


---

### 5. API Versioning
> Explain API versioning and why it's needed (you can't break existing clients when you change your API). Compare the 3 common approaches: URL versioning (`/v1/items`), header versioning (`Accept: application/vnd.myapi.v1+json`), and query param versioning. Implement URL versioning on your API (`/v1/items` → `/v2/items` with a changed response shape).

**Answer & Implementation:**

Versioning is essential because APIs evolve—new features are added, response schemas change, and internal implementations are refactored. Without versioning, changing the API breaks existing client integrations, leading to runtime errors, data inconsistencies, and lost revenue.*

*Common API Versioning Approaches*

- **URL Versioning** (`/v1/items`) : Explicit and intuitive, but pollutes the URL namespace and requires code duplication across versions.
- **Header Versioning** (`Accept: application/vnd.myapi.v1+json`): Clean URLs, better for caching, but hidden from casual browser inspection and harder to test.
- **Query Param Versioning** (`/items?version=1`): Simple to implement, easy to test, but can clutter logs and doesn't work with HTTP caching.

**Comparison of the 3 approaches:**

| Approach | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **URL Versioning** (`/v1/items`) | Explicit, intuitive, easy to test | Pollutes URL namespace, code duplication | Public APIs with breaking changes |
| **Header Versioning** (`Accept: application/vnd.myapi.v1+json`) | Clean URLs, better for caching | Hidden from casual inspection, harder to test | Internal APIs, mobile apps |
| **Query Param Versioning** (`/items?version=1`) | Simple to implement, easy to test | Clutters logs, doesn't work with caching | Quick experiments, internal tools |

**FastAPI Implementation: URL Versioning (/v1 vs /v2)**

```python
from typing import List
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

# Shared Data Store
ITEMS_DATA = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 89.99, "currency": "USD", "stock": 10},
    {"id": 2, "name": "Wireless Mouse", "price": 49.99, "currency": "USD", "stock": 0},
]

# ===========================================================================
# V1: Flat schema with scalar price and name
# ===========================================================================
class ItemResponseV1(BaseModel):
    id: int
    name: str
    price: float

router_v1 = APIRouter(prefix="/v1/items", tags=["V1"])

@router_v1.get("", response_model=List[ItemResponseV1])
def get_items_v1():
    return [
        ItemResponseV1(id=item["id"], name=item["name"], price=item["price"])
        for item in ITEMS_DATA
    ]

# ===========================================================================
# V2: Restructured schema with nested pricing and availability flag
# ===========================================================================
class PriceDetailV2(BaseModel):
    amount: float
    currency: str
    formatted: str

class ItemResponseV2(BaseModel):
    id: int
    title: str = Field(..., description="Renamed from name to title")
    pricing: PriceDetailV2 = Field(..., description="Nested price object")
    in_stock: bool

router_v2 = APIRouter(prefix="/v2/items", tags=["V2"])

@router_v2.get("", response_model=List[ItemResponseV2])
def get_items_v2():
    return [
        ItemResponseV2(
            id=item["id"],
            title=item["name"],
            pricing=PriceDetailV2(
                amount=item["price"],
                currency=item["currency"],
                formatted=f"${item['price']:.2f}"
            ),
            in_stock=item["stock"] > 0
        )
        for item in ITEMS_DATA
    ]

# App Mounting
app = FastAPI(title="Versioned API")
app.include_router(router_v1, prefix="/api")
app.include_router(router_v2, prefix="/api")

```
**Response Payloads Comparison**

V1 Response (GET /api/v1/items):

```json
[
  { "id": 1, "name": "Mechanical Keyboard", "price": 89.99 },
  { "id": 2, "name": "Wireless Mouse", "price": 49.99 }
]
```
V2 Response (GET /api/v2/items):

```json
[
  {
    "id": 1,
    "title": "Mechanical Keyboard",
    "pricing": { "amount": 89.99, "currency": "USD", "formatted": "$89.99" },
    "in_stock": true
  },
  {
    "id": 2,
    "title": "Wireless Mouse",
    "pricing": { "amount": 49.99, "currency": "USD", "formatted": "$49.99" },
    "in_stock": false
  }
]
```

---

