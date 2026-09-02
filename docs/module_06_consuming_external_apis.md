# Module 06 — Consuming External APIs (Being the Client)

## Overview
Consuming external third-party APIs using Python client libraries (`requests` / `httpx`), robust error handling, network failure resilience, exponential backoff retry algorithms, retry storm prevention, selective failure retries, secure API key management via environment variables, and client-side rate limit handling (`429 Too Many Requests`).

---

## Conceptual Questions & Answers

### 1. Consuming a Public API with Python
> Write a script using `httpx` (or `requests`) that calls a public API and parses the JSON response.

Modern Python client libraries like `httpx` support synchronous and asynchronous HTTP/1.1 and HTTP/2 requests with built-in JSON deserialization (`response.json()`), connection pooling, and request timeout configurations.

---

### 2. Comprehensive Failure & Network Error Handling
> Handle failures properly: timeouts (`timeout=5.0`), status checking (`response.raise_for_status()`), and network exceptions.

**Potential Network Failures:**
1. **API Down / DNS Resolution Failure**: Client cannot resolve host or connect socket (`ConnectError` / `ConnectionError`).
2. **Network Timeout**: Upstream takes longer than timeout threshold (`TimeoutException` / `ReadTimeout`). Without explicit timeouts, threads hang indefinitely.
3. **HTTP 4xx Client Errors**: Requested resource not found (`404`), unauthenticated (`401`), or malformed payload (`400`).
4. **HTTP 5xx Server Errors**: Upstream server crash (`500`) or gateway failure (`502`/`504`).

---

### 3. Exponential Backoff Retry Logic & Retry Storms
> Implement retry logic with exponential backoff. Explain why retrying immediately in a tight loop is bad practice (retry storm).

**Why Immediate Retries Cause Retry Storms (Cascading Outages):**
When an upstream service experiences a momentary overload or database connection exhaustion:
- Retrying immediately in a tight loop multiplies request volume when the system is least capable of handling it.
- If 1,000 concurrent clients fail and each retries immediately 3 times, the server receives 3,000 extra requests within milliseconds.
- This creates a **Retry Storm** (self-inflicted Layer-7 DDoS attack), preventing recovery.
- **Exponential Backoff** spaces out retry delays exponentially ($1\text{s}, 2\text{s}, 4\text{s}$), allowing upstream queues to drain and servers to recover.

---

### 4. Non-Retryable vs Retryable Failures
> Explain why you should not retry on every failure (e.g. 400 vs 503).

| Category | HTTP Codes / Errors | Should Retry? | Rationale |
| :--- | :--- | :--- | :--- |
| **Non-Retryable (Deterministic / Client Errors)** | `400`, `401`, `403`, `404`, `422` | **NO** | The request itself is invalid or missing credentials. Retrying the exact same request will produce the exact same error every time, wasting client and server resources. |
| **Retryable (Transient / Server Errors)** | `502`, `503`, `504`, Socket Timeouts | **YES** | The failure is caused by temporary network congestion, server reboot, or load spikes that will resolve shortly. |
| **Conditionally Retryable** | `429 Too Many Requests` | **YES (With Pause)** | Only retry after pausing for the exact seconds specified in the `Retry-After` header. |

---

### 5. Authenticated Requests & Secure Environment Configuration
> Send authenticated requests using headers. Explain why API keys belong in environment variables / `.env` and why `.env` belongs in `.gitignore`.

1. **Git Commit History is Permanent**: Secrets pushed to git remain in the commit log even if deleted later.
2. **Public Scrapers**: Automated botnets constantly scan public repositories to harvest API keys.
3. **Environment Segregation**: Development, Staging, and Production require different credentials.
4. **`.gitignore` Role**: Prevents local plaintext credentials from being checked into version control. Developers provide a `.env.example` template with dummy placeholders instead.

---

### 6. Client-Side Rate Limiting & `429 Too Many Requests`
> Explain what `429 Too Many Requests` means and how a client should handle the `Retry-After` header.

When receiving HTTP 429:
1. Parse the `Retry-After` header to extract the required cooldown duration in seconds.
2. Sleep / pause the worker thread (`time.sleep(retry_after)` or `asyncio.sleep()`) before resubmitting the request.
3. If no `Retry-After` header is returned, apply exponential backoff fallback.

---

## Practical: Resilient External API Client Implementation

### Implementation
**File:** [`src/practicals/module_06_external_client.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_06_external_client.py)  
**Tests:** [`tests/test_module_06_external_client.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_06_external_client.py)

Implemented:
1. Resilient HTTP client using `httpx` with configurable request timeouts.
2. Exponential backoff retry loop ($0.5\text{s}, 1\text{s}, 2\text{s}$) with automated retry storm avoidance.
3. Selective error classification:
   - Immediately aborts on non-retryable 4xx client errors (`401 Unauthorized`, `400 Bad Request`, `404 Not Found`).
   - Retries on transient 5xx server errors (`503 Service Unavailable`, timeouts).
4. Automated `429 Too Many Requests` handling that pauses execution for the duration specified by the server's `Retry-After` header.

### How I Ran It
```bash
python -m src.practicals.module_06_external_client
```

### Testing
```bash
pytest tests/test_module_06_external_client.py -v
```

### Result
```text
======================================================================
Module 06: Consuming External APIs — Resilient Client Practical Run
======================================================================

[1] Normal GET /posts/1 -> Success!
    Payload Title: 'Understanding Resilient API Consumption in Python'

[2] Testing Transient 503 Endpoint (Requires Retries):
    Result after backoff: {'status': 'success', 'attempt_succeeded': 3, 'data': 'Recovered successfully after backoff!'}

[3] Testing Non-Retryable 401 Unauthorized:
    Caught expected HTTPStatusError: 401 (Aborted immediately as expected)

[4] Testing 429 Rate Limiting & Retry-After:
    Result after waiting for Retry-After: {'status': 'success', 'message': 'Request processed after respecting rate limit wait.'}

======================================================================
Module 06 external client resilience tests passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Deterministic Error Differentiation**: Halting immediately on 4xx saves significant CPU cycles and network overhead by not retrying requests that are doomed to fail.
2. **Transient Error Recovery**: The client successfully recovered from two consecutive 503 Service Unavailable errors on attempt #3 after applying exponential backoff delays.
3. **Respecting `Retry-After`**: Parsing the `Retry-After` header prevents client-side guessing and guarantees that requests are retried exactly when the upstream quota replenishes.

### Issues Encountered & Fixes
- **Issue**: Distinguishing 429 (which should be retried after pause) from standard 4xx errors (which must abort immediately).
- **Fix**: Added a specific branch in the error classifier to extract `Retry-After` on status 429 before checking the 400..499 non-retryable range.
