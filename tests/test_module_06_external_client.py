"""
Tests for Module 06: Resilient External API Client Practical
"""

import httpx
import pytest
from src.practicals.module_06_external_client import (
    ResilientExternalClient,
    request_counters
)


def test_module_06_resilient_client_success():
    client = ResilientExternalClient()
    data = client.fetch_with_backoff("/posts/1")
    assert data["id"] == 1
    assert "Resilient" in data["title"]


def test_module_06_retry_backoff_and_recovery():
    request_counters["flaky_503"] = 0
    client = ResilientExternalClient()

    slept_durations = []

    def mock_sleep(d: float):
        slept_durations.append(d)

    # Should retry and succeed on attempt 3 with backoff delays
    data = client.fetch_with_backoff("/flaky-endpoint", max_retries=3, base_delay=1.0, sleep_fn=mock_sleep)
    assert data["status"] == "success"
    assert data["attempt_succeeded"] == 3
    # Verifies exponential backoff sequence: 1.0s, 2.0s
    assert slept_durations == [1.0, 2.0]


def test_module_06_non_retryable_failure_abort():
    client = ResilientExternalClient()
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        client.fetch_with_backoff("/unauthorized-endpoint", max_retries=3)
    assert exc_info.value.response.status_code == 401


def test_module_06_rate_limit_retry_after():
    request_counters["rate_limited_429"] = 0
    client = ResilientExternalClient()

    slept_durations = []

    def mock_sleep(d: float):
        slept_durations.append(d)

    data = client.fetch_with_backoff("/rate-limited-endpoint", max_retries=3, sleep_fn=mock_sleep)
    assert data["status"] == "success"
    # Verifies client slept for Retry-After duration (1.0s)
    assert slept_durations == [1.0]
