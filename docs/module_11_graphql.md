# Module 11 — GraphQL, Properly

## Overview
Understanding GraphQL as a data query and manipulation language for APIs. Exploring the Schema Definition Language (SDL), Object Types, Query root resolvers, Mutation state modifiers, eliminating over-fetching and under-fetching, and addressing the GraphQL N+1 problem with DataLoaders.

---

## Conceptual Questions & Answers

### 1. REST vs GraphQL Architectural Comparison
> Compare REST and GraphQL across data fetching efficiency, network round trips, versioning, caching complexity, and tooling.

| Feature | REST | GraphQL |
| :--- | :--- | :--- |
| **Data Fetching** | Fixed server-defined response shape per endpoint | Client requests exact fields required via query selection set |
| **Over-Fetching** | Common: Endpoint returns 30 fields when client needs only 2 | Eliminated: Network payload transmits only requested keys |
| **Under-Fetching (N+1 Calls)** | Common: Fetching user + orders + products requires 3 separate HTTP requests | Eliminated: Client fetches all related entities in 1 single query |
| **Endpoints** | Multiple resource URIs (`/users`, `/products`, `/orders`) | Single unified endpoint (`/graphql`) accepting POST requests |
| **HTTP Caching** | Native: Works with standard HTTP proxies, CDNs, `ETag`, `304 Not Modified` | Complex: Requires client-side normalized caching (Apollo / Relay) |
| **Versioning** | URL or header versioning (`/v1`, `/v2`) | Field-level evolution and `@deprecated` directives without URL changes |

---

### 2. Queries, Mutations, and Resolvers
> Explain how queries read data, mutations modify state, and resolvers bind schemas to backend data sources.

- **Types**: Define the shape and relationships of data objects in the schema (e.g. `Product`, `Order`, `OrderItem`).
- **Queries (Read Operations)**: Analogous to HTTP `GET`. Queries fetch data trees without mutating server state. Clients specify the exact fields to return:
  ```graphql
  query {
    products(category: "Electronics") {
      id
      name
      price
    }
  }
  ```
- **Mutations (Write Operations)**: Analogous to HTTP `POST`/`PUT`/`DELETE`. Mutations perform side effects (creating records, updating balances, placing orders) and return the modified entity in a single round trip:
  ```graphql
  mutation {
    createProduct(name: "Mechanical Keyboard", price: 89.99, stock: 25, category: "Electronics") {
      id
      name
    }
  }
  ```
- **Resolvers**: Functions that fetch the data for a particular field. When a client executes a query, the GraphQL execution engine calls the corresponding resolver for each field in the selection tree.

---

### 3. Over-Fetching vs Under-Fetching Solutions
- **Over-Fetching Solution**: In REST, `GET /users/1` might return 50 fields including address, preferences, and telemetry. In GraphQL, a mobile device requests only `{ id name }`, saving network bandwidth.
- **Under-Fetching Solution**: To display a user profile with their latest 3 orders and product names, REST requires 3 sequential HTTP calls: `GET /users/1` -> `GET /users/1/orders` -> `GET /products/101`. GraphQL resolves all nested relationships in a single request.

---

## Practical: Strawberry GraphQL Schema & Resolver Implementation

### Implementation
**File:** [`src/practicals/module_11_graphql_app.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_11_graphql_app.py)  
**Main App Router:** [`src/routers/graphql_router.py`](file:///c:/office%20files/api-backend-assignment/src/routers/graphql_router.py)  
**Tests:** [`tests/test_module_11_graphql.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_11_graphql.py)

Implemented:
1. Strongly-typed GraphQL Object Types (`ProductType`, `OrderItemType`, `OrderType`) using Strawberry GraphQL.
2. Query root resolvers:
   - `products(category: Optional[str])`
   - `product(id: int)`
   - `orders(userId: Optional[int])`
3. Mutation root resolvers:
   - `createProduct(name, price, stock, category)`
   - `createOrder(userId, productId, quantity)`
4. Nested resolver relationships (`OrderItem -> Product`) demonstrating sub-resource resolution.
5. Mounted Strawberry `GraphQLRouter` to FastAPI at `/graphql`.

### How I Ran It
```bash
python -m src.practicals.module_11_graphql_app
```

### Testing
```bash
pytest tests/test_module_11_graphql.py -v
```

### Result
```text
======================================================================
Module 11: GraphQL, Properly Practical Run
======================================================================

[1] GraphQL Query (Exact Fields: id, name, price) -> Status: 200
    Response Data: [{'id': 1, 'name': 'Mechanical Keyboard RGB', 'price': 89.99}, {'id': 2, 'name': 'Wireless Ergonomic Mouse', 'price': 49.99}, {'id': 3, 'name': 'Noise Cancelling Headphones', 'price': 199.99}]

[2] GraphQL Nested Query (Orders + Items + Products) -> Status: 200
    Nested Response Data: [{'id': 1, 'totalAmount': 139.98, 'status': 'COMPLETED', 'items': [{'quantity': 1, 'subtotal': 89.99, 'product': {'name': 'Mechanical Keyboard RGB', 'category': 'Electronics'}}, {'quantity': 1, 'subtotal': 49.99, 'product': {'name': 'Wireless Ergonomic Mouse', 'category': 'Electronics'}}]}]

[3] GraphQL Mutation (createProduct) -> Status: 200
    Created Product Data: {'id': 4, 'name': '4K Gaming Monitor', 'price': 349.99}

======================================================================
Module 11 GraphQL queries and mutations executed successfully!
======================================================================
```

### Observations / Learnings
1. **Field Selection Precision**: Verifying the query response confirmed that only `id`, `name`, and `price` were serialized into the JSON payload; unselected fields like `description` and `stock` were omitted by the GraphQL engine.
2. **Nested Resolution**: Strawberry resolves nested relationships (`order -> items -> product`) dynamically through resolver methods on object types.
3. **Type Safety**: Strawberry uses standard Python type hints (`@strawberry.type`, `dataclasses`) to infer GraphQL types directly without manual SDL string parsing.

### Issues Encountered & Fixes
- **Issue**: Integrating Strawberry ASGI router with existing FastAPI application prefixing.
- **Fix**: Used `strawberry.fastapi.GraphQLRouter` mounted directly to `app.include_router(graphql_router, prefix="/graphql")`.
