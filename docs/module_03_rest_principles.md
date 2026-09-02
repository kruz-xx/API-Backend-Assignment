# Module 03 — REST Principles, Done Properly

## Overview
Understanding REST (Representational State Transfer) architecture, Fielding constraints, resource naming conventions, nested sub-resources, pagination strategies, filtering/sorting/searching via query parameters, and API versioning approaches.

---

## Conceptual Questions & Answers

### 1. The Core Constraints of REST
> Explain what "REST" stands for and what the core constraints are (client-server, stateless, cacheable, uniform interface, layered system, code on demand).

**Answer:**
REST stands for **Representational State Transfer**, an architectural style formulated by Roy Fielding in 2000.

**The 6 Constraints of REST:**
1. **Client-Server**: Separation of UI concerns from data storage and business logic.
2. **Stateless**: Each client request must contain all information required to process it; the server stores no client context between requests.
3. **Cacheable**: Responses must explicitly define themselves as cacheable or non-cacheable to prevent clients from reusing stale data.
4. **Uniform Interface**: Standardized URI resource identification, manipulation through representations, self-descriptive messages, and hypermedia (HATEOAS).
5. **Layered System**: Clients cannot determine whether they are connected directly to the end server or an intermediary (proxy, gateway, CDN).
6. **Code on Demand (Optional)**: Servers can temporarily extend client functionality by transferring executable code (e.g. JavaScript).

---

### 2. REST Resource Naming Conventions & Anti-Patterns
> Explain proper REST resource naming conventions (nouns not verbs, plural collections, nesting). Rewrite 5 badly-named endpoints into proper REST style.

**Guidelines:**
- Use nouns, not verbs (`/users`, not `/getUsers`).
- Use plural collections (`/products`, not `/product`).
- Use hierarchy/nesting for sub-resources (`/users/5/orders`).
- Use standard HTTP verbs for operations (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
- Use query parameters for filtering, sorting, and pagination (`/items?category=books&sort=-price`).

#### Badly-Named Endpoints vs Proper REST Style:
| # | Bad / RPC-Style Endpoint | Proper REST Endpoint | HTTP Verb | Explanation |
| :- | :--- | :--- | :--- | :--- |
| 1 | `GET /getAllUsers` | `/users` | `GET` | Uses GET on the plural collection noun 'users' |
| 2 | `POST /user-delete/5` | `/users/5` | `DELETE` | Uses DELETE on the resource URI |
| 3 | `POST /createUser` | `/users` | `POST` | Uses POST on the collection to create a new resource |
| 4 | `GET /getUserOrders?userId=5` | `/users/5/orders` | `GET` | Nested sub-resource representing user orders |
| 5 | `POST /updateProductPrice/42` | `/products/42` | `PATCH` | Uses PATCH on the product URI with price payload |

---

### 3. Pagination & Unbounded Endpoints
> Explain pagination and why you never return all rows from a collection endpoint.

**Why Returning Unbounded Collections is Dangerous:**
1. **Memory Exhaustion (OOM)**: Loading millions of records into server memory triggers heap exhaustion and crashes the worker process.
2. **Database Saturation**: Full table scans lock tables/pages, block connection pools, and max out disk I/O.
3. **Network Latency**: Serializing and transmitting tens of megabytes of JSON causes multi-second latencies and mobile timeouts.
4. **Client Freezing**: Browsers and mobile apps freeze when attempting to parse and render excessive DOM objects.

**Offset vs Cursor Pagination:**
- **Offset/Limit (`?page=2&page_size=20`)**: Simple to implement, supports jumping to arbitrary pages, but degrades on huge offsets (`OFFSET 1000000`) and is susceptible to drift when rows are inserted concurrently.
- **Cursor-Based (`?cursor=xyz&limit=20`)**: Constant $O(1)$ query time via indexed keys, immune to pagination drift, ideal for infinite feeds.

---

### 4. API Versioning Approaches
> Compare URL versioning, Header versioning, and Query parameter versioning.

| Approach | Example | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **URL Versioning** | `/api/v1/items` | Explicit, intuitive, easy to test in browser | Pollutes URL namespace, requires route duplication | Public APIs with breaking contract changes |
| **Header Versioning** | `Accept: application/vnd.myapi.v1+json` | Clean URLs, standard content negotiation | Hidden from casual inspection, harder to test | Internal APIs, mobile apps |
| **Query Param Versioning** | `/items?version=1` | Easy to test, simple fallback | Clutters logs, poor CDN caching interaction | Rapid prototyping |

---

## Practical: REST Pagination, Filtering & Versioning Implementation

### Implementation
**File:** [`src/practicals/module_03_rest_api.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_03_rest_api.py)  
**Tests:** [`tests/test_module_03_rest.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_03_rest.py)

Implemented:
1. RESTful pagination envelope returning `total_count`, `page`, `page_size`, `total_pages`, `has_next`, `has_prev`, `next_page`, `prev_page`.
2. Advanced query parameters for category filtering, keyword search in names, and dynamic sorting (e.g. `sort=-price` descending).
3. URL API Versioning comparing `/api/v1/items` (flat schema with scalar price) vs `/api/v2/items` (restructured nested pricing object and `in_stock` boolean flag).

### How I Ran It
```bash
python -m src.practicals.module_03_rest_api
```

### Testing
```bash
pytest tests/test_module_03_rest.py -v
```

### Result
```text
======================================================================
Module 03: REST Principles, Pagination & Versioning Practical Run
======================================================================

[1] GET /api/items?page=1&page_size=3 -> Status: 200
    Total Count: 8, Has Next: True
    Page 1 Item Count: 3

[2] GET /api/items?category=books&search=harry&sort=-price -> Status: 200
    Returned Items: ['Harry Potter and the Goblet of Fire ($29.99)', 'Harry Potter and the Chamber of Secrets ($26.99)']

[3] V1 Response Schema (GET /api/v1/items):
    Sample V1 Item: {'id': 1, 'name': 'Harry Potter and the Chamber of Secrets', 'price': 26.99}

[4] V2 Response Schema (GET /api/v2/items):
    Sample V2 Item: {'id': 1, 'title': 'Harry Potter and the Chamber of Secrets', 'pricing': {'amount': 26.99, 'currency': 'USD', 'formatted': '$26.99'}, 'in_stock': True}

======================================================================
Module 03 REST pagination & versioning checks passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Generic Pagination Envelopes**: Using Pydantic's `Generic[T]` allows the same pagination envelope structure (`items: List[T]`, `pagination: PaginationMetadata`) to wrap any resource model across the entire API.
2. **Dynamic Sorting Syntax**: Implementing descending sorting via `-field` prefix provides an intuitive, query-clean interface for clients without needing separate sort direction parameters.
3. **Out-of-Bounds Handling**: When a requested page exceeds `total_pages`, the endpoint returns a clear `404 Not Found` with the maximum available page number in the error message.

### Issues Encountered & Fixes
- **Issue**: Page calculation edge cases when total count is 0.
- **Fix**: Used `math.ceil(total_count / page_size) if total_count > 0 else 1` to prevent divide-by-zero or 0 total pages.
