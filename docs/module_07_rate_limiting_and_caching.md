# Module 07 — Rate Limiting, Caching & Performance (Server Side)

## 📌 Overview
Protecting backend servers from denial of service, abuse, and noisy neighbors using rate limiting algorithms (Token Bucket, Leaky Bucket, Sliding Window Counter), and improving latency with caching strategies and HTTP caching headers (`Cache-Control`, `ETag`).

---

## 📝 Conceptual Questions & Implementation Notes

### 1. Rate Limiting Algorithms
> Explain Token Bucket vs Sliding Window Rate Limiting. Why is status code `429 Too Many Requests` returned alongside headers like `Retry-After` and `X-RateLimit-Remaining`?

**Answer:**
*(Write your explanation here)*

### 2. HTTP Caching Headers
> How do `Cache-Control: max-age=...`, `ETag`, and `If-None-Match` reduce server load and return `304 Not Modified`?

**Answer:**
*(Write your explanation here)*

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_07/` and link them below)*

```markdown
<!-- Example screenshot embed:
![Rate Limit Triggered 429](../screenshots/module_07/rate_limit_exceeded_429.png)
![Cache Hit Response Headers](../screenshots/module_07/cache_hit_headers.png)
-->
```
