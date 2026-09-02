# Module 07 — Rate Limiting, Caching & Performance (Server Side)

## Overview
Protecting backend servers from denial of service, abuse, and noisy neighbors using rate limiting algorithms (Token Bucket, Leaky Bucket, Sliding Window Counter), implementing HTTP rate limiting with standard response headers (`429 Too Many Requests`, `Retry-After`), improving server throughput and network latency via HTTP caching headers (`Cache-Control`, `ETag`, `304 Not Modified`), and identifying and eliminating N+1 database query performance bottlenecks through eager loading, joins, and batching strategies.

---

## Conceptual Questions & Answers

### 1. API Rate Limiting: Purpose, Mechanisms, and Algorithms
> Explain why an API needs rate limiting (buggy clients, deliberate abuse, multi-tenant fairness). Compare Token Bucket vs Sliding Window Rate Limiting, and explain status code `429 Too Many Requests` and headers `Retry-After` and `X-RateLimit-Remaining`.

**Why Rate Limiting is Critical:**
1. **Protection Against Accidental Client Overload**: Prevents buggy client infinite loops or aggressive retry storms from exhausting worker processes and database connection pools.
2. **Mitigation of Abuse and Denial of Service (DoS)**: Throttles credential stuffing, scraping, and application-layer DDoS attacks.
3. **Multi-Tenant Fairness (Noisy Neighbor Problem)**: Ensures high-volume tenants do not monopolize shared infrastructure.
4. **Cloud Infrastructure Cost Control**: Prevents financial spikes on autoscaling clusters and pay-per-use external APIs.

#### Comparison of Rate Limiting Algorithms:
| Algorithm | Mechanism | Advantages | Disadvantages | Time / Space |
| :--- | :--- | :--- | :--- | :--- |
| **Token Bucket** | Tokens added at rate $r$ up to capacity $C$. Each request consumes 1 token. | Handles traffic bursts up to capacity $C$; memory friendly. | Tuning fill rate and burst capacity can be complex. | $O(1) / O(1)$ |
| **Leaky Bucket** | Requests enter FIFO queue and are processed at a steady, uniform rate. | Completely smooths outgoing traffic to downstream workers. | Bursts are delayed rather than processed immediately. | $O(1) / O(C)$ |
| **Fixed Window** | Counter resets at fixed time intervals (e.g. start of each minute). | Simple, minimal memory. | **Boundary Burst Flaw**: Double capacity across window boundary. | $O(1) / O(1)$ |
| **Sliding Window Log** | Tracks exact timestamps in sorted set; removes timestamps older than window. | 100% accurate, completely eliminates boundary burst issues. | Higher memory usage (stores all timestamps). | $O(\log N) / O(N)$ |
| **Sliding Window Counter** | Combines current window count with weighted fraction of previous window. | Constant memory $O(1)$, smooths boundary spikes. | Approximation (~99.9% accurate). | $O(1) / O(1)$ |

---

### 2. HTTP Caching Headers and 304 Not Modified
> How do `Cache-Control: max-age=...`, `ETag`, and `If-None-Match` reduce server load and return `304 Not Modified`?

```text
1. Initial Request:
   Client ─── GET /api/v1/products/42 ───> Server
   Client <── 200 OK [Body: 50KB, ETag: "abc123", Cache-Control: max-age=120] ─── Server

2. Fresh Cache Window (< 120s):
   Client serves from local cache. (0ms latency, 0 server load)

3. Stale Cache / Revalidation (> 120s):
   Client ─── GET /api/v1/products/42 [If-None-Match: "abc123"] ───> Server
   Server checks entity hash. Unchanged!
   Client <── 304 Not Modified [0KB payload body] ─── Server
```

- **`Cache-Control: max-age=120, must-revalidate`**: Instructs caches that response is fresh for 120 seconds.
- **`ETag`**: Cryptographic SHA-256 hash or version tag representing resource state.
- **`If-None-Match`**: Conditional header sent by client with stored ETag.
- **`304 Not Modified`**: Sent with empty body when ETag matches, saving network bandwidth and serialization CPU.

---

### 3. The N+1 Database Query Problem
> Explain N+1 query problems conceptually and how they are fixed (SQL JOIN, batching `WHERE IN`, eager loading).

**What is the N+1 Problem?**
When fetching $N$ parent records (e.g. 100 orders), an application runs 1 initial query for orders, and then executes $N$ individual secondary queries inside a loop to fetch each user (`SELECT * FROM users WHERE id = ?`).
- **Query Count**: $1 + N$ queries ($1 + 100 = 101$ DB round-trips).
- **Remediation Strategies**:
  1. **SQL JOIN (`joinedload`)**: 1 single database query joining parent and child tables.
  2. **Batch Eager Loading (`selectinload` / `WHERE IN`)**: Exactly 2 queries (1 for parent records + 1 `SELECT ... WHERE id IN (1, 2, 3...)` for children).
  3. **DataLoader Pattern**: Batches independent resolver lookups in async/GraphQL architectures into a single batched query per tick.

---

## Practical: Rate Limiting, ETag Caching & N+1 Performance Optimization

### Implementation
**File:** [`src/practicals/module_07_rate_limit_cache.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_07_rate_limit_cache.py)  
**Tests:** [`tests/test_module_07_rate_limit_cache.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_07_rate_limit_cache.py)

Implemented:
1. In-memory Sliding Window Log Rate Limiter (5 requests per 60 seconds per API key) returning `429 Too Many Requests` with `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.
2. HTTP ETag conditional caching handler returning `304 Not Modified` with 0-byte payload on matching `If-None-Match`.
3. Executable benchmark comparing Naive N+1 query execution against SQL JOIN and Batch `WHERE IN` queries with execution tracking.

### How I Ran It
```bash
python -m src.practicals.module_07_rate_limit_cache
```

### Testing
```bash
pytest tests/test_module_07_rate_limit_cache.py -v
```

### Result
```text
======================================================================
Module 07: Rate Limiting, Caching & N+1 Performance Practical Run
======================================================================

[1] Testing Rate Limiter (5 requests allowed per minute):
    Req #1: Status 200 | Remaining: 4 | Retry-After: N/A
    Req #2: Status 200 | Remaining: 3 | Retry-After: N/A
    Req #3: Status 200 | Remaining: 2 | Retry-After: N/A
    Req #4: Status 200 | Remaining: 1 | Retry-After: N/A
    Req #5: Status 200 | Remaining: 0 | Retry-After: N/A
    Req #6: Status 429 | Remaining: 0 | Retry-After: 59

[2] Testing HTTP ETag & 304 Not Modified Caching:
    Initial Request: Status 200 OK | Received ETag: "0feed1079646b17188845637a0246dd2a48b522815b40eb53555a3113891a818"
    Conditional Request: Status 304 Not Modified | Content-Length: 0 bytes (0 bytes payload)

[3] Testing N+1 Query Optimization Benchmark:
    Naive N+1 Queries Fired: 6 (Anti-Pattern: 1 initial + 5 child queries)
    SQL JOIN Queries Fired:  1 (Optimized: 1 query)
    Batch WHERE IN Queries:  2 (Optimized: 2 queries)

======================================================================
Module 07 rate limiting, caching & N+1 optimization checks passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Sliding Window Accuracy**: The sliding window log accurately calculated that exactly 59 seconds remained before the client's oldest request would expire from the rolling 60-second window.
2. **Zero-Byte 304 Payload**: When the client provided a matching ETag in `If-None-Match`, the server bypassed body serialization and immediately returned HTTP 304 with `Content-Length: 0`.
3. **N+1 Query Reduction**: Demonstrating the benchmark showed an 83% reduction in database queries (from 6 queries down to 1) when switching from naive looping to relational joins.

### Issues Encountered & Fixes
- **Issue**: Timestamp queue eviction logic when requests arrive across rolling window boundaries.
- **Fix**: Used `deque.popleft()` inside a `while` loop comparing against `current_time - window_seconds`.
