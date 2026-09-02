"""
Tests for Module 07: Rate Limiting, Caching & Performance Practical
"""

from fastapi.testclient import TestClient
from src.practicals.module_07_rate_limit_cache import (
    app,
    limiter,
    run_n_plus_one_benchmark
)


def test_module_07_sliding_window_rate_limiting():
    limiter._clients.clear()
    client = TestClient(app)
    api_key = "pytest_tier_gold"

    # Send 5 requests (within limit) -> All 200 OK
    for _ in range(5):
        res = client.get("/api/v1/analytics/report", headers={"X-API-Key": api_key})
        assert res.status_code == 200
        assert "X-RateLimit-Limit" in res.headers

    # 6th request exceeds limit -> 429 Too Many Requests with Retry-After header
    res_6th = client.get("/api/v1/analytics/report", headers={"X-API-Key": api_key})
    assert res_6th.status_code == 429
    assert "Retry-After" in res_6th.headers
    assert res_6th.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_module_07_etag_conditional_caching():
    client = TestClient(app)

    # Initial request
    res_init = client.get("/api/v1/products/prod_101")
    assert res_init.status_code == 200
    etag = res_init.headers.get("ETag")
    assert etag is not None

    # Conditional request with matching If-None-Match header
    res_cond = client.get("/api/v1/products/prod_101", headers={"If-None-Match": etag})
    assert res_cond.status_code == 304
    assert len(res_cond.content) == 0


def test_module_07_n_plus_one_benchmark_counts():
    bench = run_n_plus_one_benchmark()
    # Naive executes 1 parent query + 5 child queries = 6 queries
    assert bench["naive_query_count"] == 6
    # SQL JOIN executes 1 query
    assert bench["join_query_count"] == 1
    # Batch WHERE IN executes 2 queries
    assert bench["batch_query_count"] == 2
