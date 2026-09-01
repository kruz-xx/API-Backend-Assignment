# Module 06 — Consuming External APIs (Being the Client)

## Overview
Consuming external third-party APIs using Python client libraries (`requests` / `httpx`), robust error handling, network failure resilience, exponential backoff retry algorithms, retry storm prevention, selective failure retries, secure API key management via environment variables, and client-side rate limit handling (`429 Too Many Requests`).

---

## Conceptual Questions & Implementation Notes

### 1. Consuming a Public API with Python
> Using Python's `requests` (or `httpx`) library, write a script that calls a real public API (e.g. a free weather API, or `https://jsonplaceholder.typicode.com`) and prints the parsed JSON response.

**Answer & Implementation:**

```python
import httpx
import json

def fetch_post_data(post_id: int = 1) -> dict:
    """
    Fetches a post resource from the JSONPlaceholder public REST API.
    """
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    
    with httpx.Client() as client:
        response = client.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
    return data

if __name__ == "__main__":
    post = fetch_post_data(1)
    print("Parsed JSON Response:")
    print(json.dumps(post, indent=2))
```

**Parsed JSON Output:**
```json
{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
}
```

---

### 2. Comprehensive Failure & Network Error Handling
> Handle failure properly: what happens if the API is down, the network times out, or it returns a 4xx/5xx? Add explicit timeout handling (`requests.get(url, timeout=5)`), status code checking (`response.raise_for_status()`), and a try/except around network errors.

**Answer & Implementation:**

**Potential Network Failures:**
1. **API Down / DNS Resolution Failure:** Client cannot resolve the hostname or establish a socket connection (`ConnectionError` / `ConnectError`).
2. **Network Timeout:** The server takes longer than the allotted timeout threshold to establish a connection or send response bytes (`TimeoutException` / `ReadTimeout`). Without explicit timeouts, requests can hang indefinitely, exhausting worker threads.
3. **HTTP 4xx Client Errors:** The requested resource was not found (`404`), the client was unauthorized (`401`), or sent invalid data (`400`).
4. **HTTP 5xx Server Errors:** The upstream server crashed (`500`) or upstream gateway timed out (`502`/`504`).

**Robust Implementation:**

```python
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_api_call(url: str, timeout_seconds: float = 5.0) -> dict:
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(url)
            # Raises HTTPStatusError if status_code is 4xx or 5xx
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        logger.error("Request timed out after %s seconds: %s", timeout_seconds, exc)
        raise RuntimeError("External service timed out. Please try again later.") from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        logger.error("HTTP error occurred: %s %s - %s", status_code, exc.response.reason_phrase, exc.response.text)
        if 400 <= status_code < 500:
            raise ValueError(f"Client request error ({status_code}): {exc.response.text}") from exc
        else:
            raise RuntimeError(f"External service failure ({status_code}).") from exc

    except httpx.NetworkError as exc:
        logger.error("Network / Connection failure: %s", exc)
        raise RuntimeError("Could not connect to external service. Check DNS or network connectivity.") from exc

    except httpx.RequestError as exc:
        logger.error("General request error: %s", exc)
        raise RuntimeError(f"An error occurred while requesting {exc.request.url}.") from exc
```

---

### 3. Exponential Backoff Retry Logic & Retry Storms
> Implement **retry logic with exponential backoff**: if a request fails (especially 5xx or a timeout), retry up to 3 times, waiting progressively longer between attempts (e.g. 1s, 2s, 4s). Explain why retrying immediately in a tight loop is bad practice (can make an already-struggling server worse — this is called a "retry storm").

**Answer & Implementation:**

**Why Retrying Immediately in a Tight Loop is Bad Practice ("Retry Storm"):**
When an upstream server experiences degraded performance, database connection pool exhaustion, or high traffic spikes:
- Immediate retries in a tight loop (`while True: get()`) send multiplied bursts of requests when the server is already overloaded.
- If 1,000 concurrent clients fail and each immediately retries 3 times, the server receives 3,000 additional requests within milliseconds.
- This creates a **Retry Storm (Cascading Failure)**, effectively executing a self-inflicted Distributed Denial of Service (DDoS) attack that prevents the server from recovering.
- **Exponential Backoff** spaces out retry attempts exponentially (e.g., $1\text{s}, 2\text{s}, 4\text{s}$), giving the downstream service time to recover and clear queues.

**Python Implementation with Exponential Backoff:**

```python
import time
import httpx
import logging

logger = logging.getLogger(__name__)

def fetch_with_exponential_backoff(
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 5.0
) -> dict:
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                
                # Check status code; retry on 5xx server errors
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response
                    )
                
                response.raise_for_status()
                return response.json()

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_exception = exc
            
            # Do not retry on 4xx client errors (except possibly 429)
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                logger.error("Non-retryable client error %s. Aborting retries.", exc.response.status_code)
                raise exc

            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))  # 1s, 2s, 4s
                logger.warning(
                    "Attempt %d/%d failed with error '%s'. Retrying in %.2f seconds...",
                    attempt, max_retries, exc, delay
                )
                time.sleep(delay)
            else:
                logger.error("All %d retry attempts failed.", max_retries)

    raise RuntimeError(f"Max retries ({max_retries}) exceeded.") from last_exception
```

---

### 4. Non-Retryable vs Retryable Failures
> Explain why you should generally **not** retry on every failure — e.g. retrying a 400 Bad Request is pointless (the request itself is wrong, retrying won't fix it), but retrying a 503 Service Unavailable or a timeout makes sense.

**Answer:**

**Failure Classification:**

| Category | HTTP Codes / Errors | Should Retry? | Rationale |
| :--- | :--- | :--- | :--- |
| **Non-Retryable (Deterministic / Client Errors)** | `400 Bad Request`<br>`401 Unauthorized`<br>`403 Forbidden`<br>`404 Not Found`<br>`422 Unprocessable Entity` | **NO** | The request was malformed, missing fields, or lacked credentials. Retrying the exact same request will yield the exact same error 100% of the time, wasting network and server resources. |
| **Retryable (Transient / Server & Network Errors)** | `502 Bad Gateway`<br>`503 Service Unavailable`<br>`504 Gateway Timeout`<br>Socket Timeouts<br>Connection Resets | **YES** | The error is caused by temporary network blips, upstream load, rolling deployments, or transient infrastructure congestion that will resolve shortly. |
| **Conditionally Retryable (Rate Limits)** | `429 Too Many Requests` | **YES (With Pause)** | Only retry after waiting for the duration specified in the `Retry-After` header. Do not retry with immediate backoff. |

---

### 5. Authenticated Requests & Secure Environment Configuration
> Send authenticated requests to an external API using an API key or bearer token in the headers. Explain why API keys should never be hardcoded in source code — use environment variables (`os.environ`) or a `.env` file (and explain why `.env` belongs in `.gitignore`).

**Answer & Implementation:**

**Why API Keys Must Never Be Hardcoded in Source Code:**
1. **Git History Exposure:** Once committed, secrets remain in Git commit history permanently, even if removed in subsequent commits.
2. **Public Repository Leakage:** Automated bots constantly scrape public GitHub/GitLab repositories for API keys (e.g., AWS, OpenAI, Stripe) and exploit them within seconds.
3. **Environment Separation:** Different environments (Local Development, Staging, Production) require distinct API credentials. Hardcoding prevents multi-stage deployments.
4. **Why `.env` Belongs in `.gitignore`:** The `.env` file contains sensitive plaintext credentials specific to the developer's local machine or secret store. Putting `.env` in `.gitignore` prevents local secrets from being checked into version control. Instead, commit a `.env.example` file with dummy values for documentation.

**Authenticated Client Implementation:**

```python
import os
import httpx
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

API_BASE_URL = os.getenv("EXTERNAL_SERVICE_URL", "https://api.example.com/v1")
API_KEY = os.getenv("EXTERNAL_SERVICE_API_KEY")

if not API_KEY:
    raise ValueError("EXTERNAL_SERVICE_API_KEY environment variable is not configured.")

def query_external_secured_service(endpoint: str, payload: dict) -> dict:
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "BackendIntegrationClient/1.0"
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

---

### 6. Client-Side Rate Limiting & `429 Too Many Requests`
> Explain **rate limiting from the consumer's perspective**: what does it mean when an API returns `429 Too Many Requests`, and what should your client do about it (check `Retry-After` header, etc.).

**Answer:**

**What HTTP `429 Too Many Requests` Means:**
The `429 Too Many Requests` status code indicates that the client has sent too many requests in a given amount of time ("rate limit exceeded"). The upstream server refuses to process additional requests until the rate quota window resets.

**Upstream Rate-Limiting Headers:**
- `Retry-After`: The number of seconds to wait (or an HTTP date) before making a new request (e.g., `Retry-After: 30`).
- `X-RateLimit-Limit`: Maximum allowed requests within the current window (e.g., `100`).
- `X-RateLimit-Remaining`: Remaining request quota in the current window (e.g., `0`).
- `X-RateLimit-Reset`: Unix timestamp when the current rate quota resets.

**What the Client Application Should Do:**
1. **Parse `Retry-After` Header:** Extract the wait duration from the `Retry-After` header. If absent, apply a default backoff delay.
2. **Pause Execution:** Sleep or delay scheduled tasks for the requested duration (`time.sleep(retry_after)` or `asyncio.sleep()`).
3. **Client-Side Throttling:** Implement client-side token bucket or leaky bucket rate limiters to prevent hitting upstream limits proactively.
4. **Queue & Batch Requests:** Aggregate high-frequency single requests into batch operations if supported by the provider.

**Client Handling Implementation:**

```python
import time
import httpx
import logging

logger = logging.getLogger(__name__)

def request_with_rate_limit_handling(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        with httpx.Client() as client:
            response = client.get(url)
            
            if response.status_code == 429:
                retry_after_str = response.headers.get("Retry-After")
                if retry_after_str:
                    wait_time = float(retry_after_str)
                else:
                    wait_time = 2.0 ** attempt  # Default fallback backoff
                
                logger.warning(
                    "Rate limited (429). Server requested wait of %.2f seconds. Pausing execution...",
                    wait_time
                )
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()
            
    raise RuntimeError("Failed request due to persistent 429 rate limiting.")
```

---

## Execution Proof

```bash
# Execute external client test script
python -c "
import httpx
res = httpx.get('https://jsonplaceholder.typicode.com/posts/1', timeout=5.0)
print('Status:', res.status_code)
print('Title:', res.json()['title'])
"
```
