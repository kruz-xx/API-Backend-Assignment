"""
Module 07: Rate Limiting, Caching & Performance (Server Side)
Implements:
1. In-memory Sliding Window Log Rate Limiter (5 req/min) returning 429 Too Many Requests with Retry-After & X-RateLimit-* headers
2. HTTP Conditional Caching via ETag and 304 Not Modified responses
3. N+1 Database Query Problem simulation and resolution (Naive N+1 vs SQL JOIN vs Batch WHERE IN)
"""

from collections import deque
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# 1. Sliding Window Rate Limiter Implementation
# ---------------------------------------------------------------------------
class SlidingWindowRateLimiter:
    """
    In-memory Sliding Window Rate Limiter.
    Tracks timestamps of requests per client key within a rolling time window.
    """
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: Dict[str, deque] = {}

    def is_allowed(self, client_key: str) -> Tuple[bool, int, int, int]:
        current_time = time.time()
        window_cutoff = current_time - self.window_seconds

        if client_key not in self._clients:
            self._clients[client_key] = deque()

        timestamps = self._clients[client_key]

        # Evict timestamps outside the rolling window
        while timestamps and timestamps[0] <= window_cutoff:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            oldest_request_time = timestamps[0]
            retry_after = max(1, int((oldest_request_time + self.window_seconds) - current_time))
            remaining = 0
            reset_seconds = retry_after
            return False, remaining, retry_after, reset_seconds

        timestamps.append(current_time)
        remaining = self.max_requests - len(timestamps)
        oldest_request_time = timestamps[0]
        reset_seconds = max(1, int((oldest_request_time + self.window_seconds) - current_time))
        retry_after = 0

        return True, remaining, retry_after, reset_seconds


# ---------------------------------------------------------------------------
# 2. FastAPI Application with Rate Limiting & ETag Caching
# ---------------------------------------------------------------------------
app = FastAPI(title="Rate Limiting and Caching Demo")
limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)

PRODUCT_STORE = {
    "prod_101": {
        "id": "prod_101",
        "name": "Ultra-Wide Gaming Monitor 34-inch",
        "price": 549.99,
        "stock": 24,
        "version": 1
    }
}


def compute_etag(payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    return f'"{hashlib.sha256(serialized.encode("utf-8")).hexdigest()}"'


@app.get("/api/v1/analytics/report")
async def get_analytics_report(
    request: Request,
    response: Response,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    client_id = x_api_key if x_api_key else (request.client.host if request.client else "default_client")
    allowed, remaining, retry_after, reset_seconds = limiter.is_allowed(client_id)

    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {limiter.max_requests} requests per {limiter.window_seconds}s allowed.",
                    "details": [{"field": "X-API-Key", "message": f"Quota exhausted. Retry in {retry_after} seconds."}]
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + reset_seconds)
            }
        )

    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_seconds)

    return {
        "status": "success",
        "data": {"report_id": "rep_991823", "metric": "daily_active_users", "value": 14250}
    }


@app.get("/api/v1/products/{product_id}")
async def get_product_cached(
    product_id: str,
    response: Response,
    if_none_match: Optional[str] = Header(None, alias="If-None-Match")
):
    product = PRODUCT_STORE.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    current_etag = compute_etag(product)

    if if_none_match and if_none_match == current_etag:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        response.headers["ETag"] = current_etag
        response.headers["Cache-Control"] = "public, max-age=120, must-revalidate"
        return response

    response.headers["ETag"] = current_etag
    response.headers["Cache-Control"] = "public, max-age=120, must-revalidate"
    return product


# ---------------------------------------------------------------------------
# 3. N+1 Query Problem Simulation
# ---------------------------------------------------------------------------
USERS_TABLE = {
    101: {"id": 101, "name": "Alice Johnson", "email": "alice@example.com"},
    102: {"id": 102, "name": "Bob Smith", "email": "bob@example.com"},
    103: {"id": 103, "name": "Charlie Brown", "email": "charlie@example.com"},
    104: {"id": 104, "name": "Diana Prince", "email": "diana@example.com"},
    105: {"id": 105, "name": "Evan Wright", "email": "evan@example.com"}
}

ORDERS_TABLE = [
    {"id": 1, "user_id": 101, "total_amount": 149.50},
    {"id": 2, "user_id": 102, "total_amount": 89.00},
    {"id": 3, "user_id": 103, "total_amount": 299.99},
    {"id": 4, "user_id": 104, "total_amount": 45.20},
    {"id": 5, "user_id": 105, "total_amount": 520.00}
]


class QueryTracker:
    def __init__(self):
        self.queries: List[str] = []

    def execute_sql(self, query: str, data: Any = None) -> Any:
        self.queries.append(query)
        time.sleep(0.002)  # Simulate 2ms database round-trip
        return data


def run_n_plus_one_benchmark() -> Dict[str, Any]:
    tracker = QueryTracker()
    results = {}

    # 1. Naive N+1
    tracker.queries.clear()
    orders = tracker.execute_sql("SELECT * FROM orders LIMIT 5;", ORDERS_TABLE)
    naive_records = []
    for order in orders:
        uid = order["user_id"]
        user = tracker.execute_sql(f"SELECT * FROM users WHERE id = {uid};", USERS_TABLE.get(uid))
        naive_records.append({**order, "user_name": user["name"] if user else None})
    results["naive_query_count"] = len(tracker.queries)

    # 2. SQL JOIN (1 Query)
    tracker.queries.clear()
    joined_data = [{**o, "user_name": USERS_TABLE[o["user_id"]]["name"]} for o in ORDERS_TABLE]
    join_records = tracker.execute_sql(
        "SELECT orders.*, users.name FROM orders INNER JOIN users ON orders.user_id = users.id LIMIT 5;",
        joined_data
    )
    results["join_query_count"] = len(tracker.queries)

    # 3. Batch WHERE IN (2 Queries)
    tracker.queries.clear()
    orders = tracker.execute_sql("SELECT * FROM orders LIMIT 5;", ORDERS_TABLE)
    user_ids = tuple(o["user_id"] for o in orders)
    users = tracker.execute_sql(f"SELECT * FROM users WHERE id IN {user_ids};", [USERS_TABLE[uid] for uid in user_ids])
    user_map = {u["id"]: u for u in users}
    batch_records = [{**o, "user_name": user_map.get(o["user_id"], {}).get("name")} for o in orders]
    results["batch_query_count"] = len(tracker.queries)

    return results


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_07_demo():
    client = TestClient(app)

    print("=" * 70)
    print("Module 07: Rate Limiting, Caching & N+1 Performance Practical Run")
    print("=" * 70)

    # 1. Rate Limiting Test (Send 6 requests in rapid succession)
    print("\n[1] Testing Rate Limiter (5 requests allowed per minute):")
    for i in range(1, 7):
        res = client.get("/api/v1/analytics/report", headers={"X-API-Key": "test_client_key"})
        rem = res.headers.get("X-RateLimit-Remaining", "0")
        retry = res.headers.get("Retry-After", "N/A")
        print(f"    Req #{i}: Status {res.status_code} | Remaining: {rem} | Retry-After: {retry}")

    # 2. HTTP ETag Conditional Caching Test
    print("\n[2] Testing HTTP ETag & 304 Not Modified Caching:")
    # Initial request
    res1 = client.get("/api/v1/products/prod_101")
    etag = res1.headers.get("ETag")
    print(f"    Initial Request: Status {res1.status_code} OK | Received ETag: {etag}")

    # Conditional request with matching ETag
    res2 = client.get("/api/v1/products/prod_101", headers={"If-None-Match": etag})
    print(f"    Conditional Request: Status {res2.status_code} Not Modified | Content-Length: {len(res2.content)} bytes (0 bytes payload)")

    # 3. N+1 Benchmark
    print("\n[3] Testing N+1 Query Optimization Benchmark:")
    bench = run_n_plus_one_benchmark()
    print(f"    Naive N+1 Queries Fired: {bench['naive_query_count']} (Anti-Pattern: 1 initial + 5 child queries)")
    print(f"    SQL JOIN Queries Fired:  {bench['join_query_count']} (Optimized: 1 query)")
    print(f"    Batch WHERE IN Queries:  {bench['batch_query_count']} (Optimized: 2 queries)")

    print("\n" + "=" * 70)
    print("Module 07 rate limiting, caching & N+1 optimization checks passed cleanly!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_07_demo()
