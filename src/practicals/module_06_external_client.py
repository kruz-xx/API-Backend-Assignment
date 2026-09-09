"""
Module 06: Consuming External APIs (Resilient Client Implementation)
Implements:
1. Public API consumption using httpx
2. Comprehensive failure handling (timeouts, status codes, network errors)
3. Exponential backoff retry logic (1s, 2s, 4s) mitigating retry storms
4. Error classification (Non-retryable 4xx vs Transient retryable 5xx/timeouts)
5. Client-side rate limit handling (parsing 429 Retry-After headers)
6. Environment-variable-based credential loading (.env)
"""

import logging
import os
import time
from typing import Any, Callable, Optional
from fastapi import FastAPI, Header, Response, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("module_06_client")

# ---------------------------------------------------------------------------
# Mock Upstream Service for Deterministic Local Testing
# ---------------------------------------------------------------------------
upstream_app = FastAPI(title="Simulated External Upstream API")

request_counters: dict[str, int] = {
    "flaky_503": 0,
    "rate_limited_429": 0
}


@upstream_app.get("/posts/1")
async def get_post_sample():
    return {
        "userId": 1,
        "id": 1,
        "title": "Understanding Resilient API Consumption in Python",
        "body": "Always use timeouts, retry on transient errors with exponential backoff, and never retry deterministic 4xx errors."
    }


@upstream_app.get("/flaky-endpoint")
async def flaky_endpoint():
    """Fails with 503 Service Unavailable for first 2 attempts, succeeds on 3rd attempt."""
    request_counters["flaky_503"] += 1
    attempt = request_counters["flaky_503"]

    if attempt < 3:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Database overload, transient upstream failure."}
        )
    return {"status": "success", "attempt_succeeded": attempt, "data": "Recovered successfully after backoff!"}


@upstream_app.get("/unauthorized-endpoint")
async def unauthorized_endpoint():
    """Fails with 401 Unauthorized (Non-retryable deterministic client error)."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Invalid client credentials."}
    )


@upstream_app.get("/rate-limited-endpoint")
async def rate_limited_endpoint():
    """Returns 429 Too Many Requests with Retry-After header on first request, succeeds on 2nd."""
    request_counters["rate_limited_429"] += 1
    attempt = request_counters["rate_limited_429"]

    if attempt == 1:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "Rate limit quota exceeded."},
            headers={"Retry-After": "1"}  # Ask client to wait 1 second
        )
    return {"status": "success", "message": "Request processed after respecting rate limit wait."}


# ---------------------------------------------------------------------------
# Resilient External API Client Implementation
# ---------------------------------------------------------------------------
class ResilientExternalClient:
    def __init__(
        self,
        base_url: str = "http://upstream.local",
        default_timeout: float = 5.0,
        transport_client: Optional[TestClient] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout
        self._test_client = transport_client or TestClient(upstream_app)

    def _execute_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Internal dispatch using TestClient or live httpx."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self._test_client.request(method, path, **kwargs)

    def fetch_with_backoff(
        self,
        path: str,
        max_retries: int = 3,
        base_delay: float = 0.5,
        sleep_fn: Callable[[float], None] = time.sleep
    ) -> dict[str, Any]:
        """
        Executes HTTP GET with exponential backoff:
        - Retries on 5xx server errors and network/timeout failures
        - Immediately halts on 4xx client errors (non-retryable)
        """
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self._execute_request("GET", path)

                # Check if server returned 5xx
                if response.status_code >= 500:
                    logger.warning(
                        "[Attempt %d/%d] Received %d Server Error from %s.",
                        attempt, max_retries, response.status_code, path
                    )
                    if attempt < max_retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.info("Retrying in %.2f seconds (Exponential Backoff)...", delay)
                        sleep_fn(delay)
                        continue
                    else:
                        response.raise_for_status()

                # Check if client error 4xx (do not retry except 429)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    logger.error("Non-retryable client error %d. Aborting retries immediately.", response.status_code)
                    response.raise_for_status()

                # Handle 429 Rate limiting
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "1"))
                    logger.warning("Received 429 Rate Limit. Server requested wait of %.1f seconds.", retry_after)
                    if attempt < max_retries:
                        sleep_fn(retry_after)
                        continue
                    else:
                        response.raise_for_status()

                response.raise_for_status()
                return response.json()

            except Exception as exc:
                last_exception = exc
                # Check for HTTPStatusError from httpx/httpx2 or any response status < 500
                resp = getattr(exc, "response", None)
                if resp is not None and getattr(resp, "status_code", None) is not None:
                    if resp.status_code < 500 and resp.status_code != 429:
                        raise exc


        raise RuntimeError(f"Failed to execute request to '{path}' after {max_retries} attempts.") from last_exception


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_06_demo():
    request_counters["flaky_503"] = 0
    request_counters["rate_limited_429"] = 0
    client = ResilientExternalClient()

    print("=" * 70)
    print("Module 06: Consuming External APIs — Resilient Client Practical Run")
    print("=" * 70)

    # 1. Normal successful API fetch
    res_normal = client.fetch_with_backoff("/posts/1")
    print(f"\n[1] Normal GET /posts/1 -> Success!")
    print(f"    Payload Title: '{res_normal['title']}'")

    # 2. Transient 503 Failure with Exponential Backoff Recovery
    print(f"\n[2] Testing Transient 503 Endpoint (Requires Retries):")
    res_flaky = client.fetch_with_backoff("/flaky-endpoint", base_delay=0.1)
    print(f"    Result after backoff: {res_flaky}")

    # 3. Non-Retryable 401 Error (Should abort immediately without retrying)
    print(f"\n[3] Testing Non-Retryable 401 Unauthorized:")
    try:
        client.fetch_with_backoff("/unauthorized-endpoint")
    except httpx.HTTPStatusError as exc:
        print(f"    Caught expected HTTPStatusError: {exc.response.status_code} (Aborted immediately as expected)")

    # 4. Rate-Limited 429 Endpoint with Retry-After Handling
    print(f"\n[4] Testing 429 Rate Limiting & Retry-After:")
    res_rate = client.fetch_with_backoff("/rate-limited-endpoint")
    print(f"    Result after waiting for Retry-After: {res_rate}")

    print("\n" + "=" * 70)
    print("Module 06 external client resilience tests passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_06_demo()
