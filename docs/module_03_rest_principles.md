# Module 03 — REST Principles, Done Properly

## 📌 Overview
Understanding Richardson Maturity Model, architectural constraints of REST (Representational State Transfer), naming conventions for URI resources, pluralization, nested resources, and avoiding RPC-style antipatterns.

---

## 📝 Conceptual Questions & Implementation Notes

### 1. The Core Constraints of REST
> What does "REST" stand for? Explain the 6 architectural constraints: Client-Server, Stateless, Cacheable, Layered System, Code on Demand (optional), and Uniform Interface.

**Answer:**
*(Write your explanation here)*

### 2. Resource Naming Conventions & Anti-patterns
> Why should endpoints be named with nouns (`/products`) instead of verbs (`/getProducts`, `/deleteProduct`)? How are sub-resources represented (e.g., `/users/{id}/orders`)?

**Answer:**
*(Write your explanation here)*

### 3. CRUD Mapping Table
| Operation | HTTP Verb | URI Path | Expected Status Code |
| :--- | :--- | :--- | :--- |
| Create Product | `POST` | `/products` | `201 Created` |
| List Products | `GET` | `/products` | `200 OK` |
| Get Product | `GET` | `/products/{id}` | `200 OK` |
| Update (Full) | `PUT` | `/products/{id}` | `200 OK` |
| Update (Partial) | `PATCH` | `/products/{id}` | `200 OK` |
| Delete Product | `DELETE` | `/products/{id}` | `204 No Content` |

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_03/` and link them below)*

```markdown
<!-- Example screenshot embed:
![CRUD Endpoints Tested](../screenshots/module_03/crud_operations_test.png)
-->
```
