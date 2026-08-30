# Module 03 — REST Principles, Done Properly

## Overview
Understanding REST (Representational State Transfer) architecture, Fielding constraints, resource naming conventions, nested sub-resources, pagination strategies, filtering/sorting/searching via query parameters, and API versioning approaches.

---

## Conceptual Questions & Implementation Notes

### 1. The Core Constraints of REST
> Explain what "REST" actually stands for and what the core constraints are (client-server, stateless, cacheable, uniform interface, layered system). You don't need to memorize the Fielding dissertation — just understand the spirit.

**Answer:**


---

### 2. REST Resource Naming Conventions & Anti-Patterns
> Explain proper REST resource naming conventions: nouns not verbs (`/users` not `/getUsers`), plural collections, nesting for relationships (`/users/5/orders`). Rewrite 5 badly-named endpoints (`/getAllUsers`, `/user-delete/5`, etc.) into proper REST style.

**Answer:**
*(Write your explanation here)*

#### Badly-Named Endpoints vs Proper REST Style:
| # | Bad / RPC-Style Endpoint | Proper REST Endpoint | HTTP Verb | Explanation |
| :- | :--- | :--- | :--- | :--- |
| 1 | `GET /getAllUsers` | *(Your answer)* | `GET` | *(Your explanation)* |
| 2 | `POST /user-delete/5` | *(Your answer)* | `DELETE` | *(Your explanation)* |
| 3 | `POST /createUser` | *(Your answer)* | `POST` | *(Your explanation)* |
| 4 | `GET /getUserOrders?userId=5` | *(Your answer)* | `GET` | *(Your explanation)* |
| 5 | `POST /updateProductPrice/42` | *(Your answer)* | `PATCH` / `PUT` | *(Your explanation)* |

---

### 3. Pagination & Unbounded Endpoints
> Explain pagination and why you'd never return "all 2 million rows" from a `GET /users` endpoint. Implement `GET /items?page=2&page_size=20` (or cursor-based pagination) on your CRUD API from Module 2, and return metadata (`total_count`, `next_page`) alongside the results.

**Answer & Implementation:**
*(Write your explanation and implementation notes here)*

```python
# Insert your paginated endpoint code and response schema here
```

---

### 4. Filtering, Sorting, and Searching via Query Parameters
> Explain filtering, sorting, and searching via query params: `GET /items?category=books&sort=-price&search=harry`. Implement at least filtering and sorting on your endpoint.

**Answer & Implementation:**
*(Write your explanation and implementation notes here)*

```python
# Insert your filtering, sorting, and searching endpoint implementation here
```

---

### 5. API Versioning
> Explain API versioning and why it's needed (you can't break existing clients when you change your API). Compare the 3 common approaches: URL versioning (`/v1/items`), header versioning (`Accept: application/vnd.myapi.v1+json`), and query param versioning. Implement URL versioning on your API (`/v1/items` → `/v2/items` with a changed response shape).

**Answer & Implementation:**
*(Write your explanation and implementation notes here)*

```python
# Insert your /v1/items and /v2/items versioning implementation here
```

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_03/` and link them below)*

```markdown
<!-- Example screenshot embed:
![Pagination and Filtering](../screenshots/module_03/pagination_filtering.png)
![API Versioning V1 vs V2](../screenshots/module_03/api_versioning.png)
-->
```
