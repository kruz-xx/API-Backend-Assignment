# Module 11 — GraphQL, Properly

## 📌 Overview
Understanding GraphQL as an alternative API architectural style to REST. Schema Definition Language (SDL), Types, Queries, Mutations, Resolvers, solving Over-fetching & Under-fetching, and the N+1 query problem.

---

## 📝 Conceptual Questions & Implementation Notes

### 1. REST vs GraphQL Comparison
> Compare REST and GraphQL across data fetching efficiency, network requests, versioning, caching complexity, and tooling.

| Feature | REST | GraphQL |
| :--- | :--- | :--- |
| **Data Fetching** | Fixed response per endpoint | Client asks for exact fields required |
| **Over/Under-fetching** | Common risk with generic endpoints | Eliminated on the network payload level |
| **Endpoints** | Multiple resource-specific URLs | Single endpoint (`/graphql`) |
| **HTTP Caching** | Native via HTTP headers (`ETag`, `Cache-Control`) | Complex, requires client/application-level cache |

---

### 2. Queries, Mutations, and Resolvers
> Explain how queries read data, mutations modify state, and resolvers bind schemas to backend data sources.

**Answer:**
*(Write your explanation and implementation notes here)*

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_11/` and link them below)*

```markdown
<!-- Example screenshot embed:
![GraphQL GraphiQL Query](../screenshots/module_11/graphiql_query_result.png)
-->
```
