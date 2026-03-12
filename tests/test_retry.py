#!/usr/bin/env python3
"""Tests for rate limit retry logic."""
from __future__ import annotations

import pytest
from helpers import make_response

from sync_forks.retry import RateLimitExhaustedError, RateLimitRetrier


def _rl_resp(remaining: str = "0", retry_after: str | None = None) -> object:
    """Build a rate-limited response with headers."""
    resp = make_response()
    resp.status_code = 429
    resp.headers["x-ratelimit-remaining"] = remaining
    if retry_after is not None:
        resp.headers["retry-after"] = retry_after
    return resp


def test_first_retry_uses_header_wait() -> None:
    """First retry determines wait from headers."""
    waits: list[int] = []
    retrier = RateLimitRetrier(on_rate_limit=waits.append)
    resp = _rl_resp(retry_after="30")
    wait = retrier.handle(resp)
    assert wait == 30
    assert waits == [30]


def test_subsequent_retry_uses_max_of_header_and_backoff() -> None:
    """Subsequent retries use max(header_wait, doubled_previous)."""
    waits: list[int] = []
    retrier = RateLimitRetrier(on_rate_limit=waits.append)
    retrier.handle(_rl_resp(retry_after="10"))
    wait2 = retrier.handle(_rl_resp(retry_after="5"))
    assert wait2 == 20  # max(5, 10*2) = 20


def test_backoff_respects_larger_header() -> None:
    """Header-suggested wait used when larger than backoff."""
    waits: list[int] = []
    retrier = RateLimitRetrier(on_rate_limit=waits.append)
    retrier.handle(_rl_resp(retry_after="10"))
    wait2 = retrier.handle(_rl_resp(retry_after="50"))
    assert wait2 == 50  # max(50, 10*2) = 50


def test_max_retries_raises() -> None:
    """After 10 retries, RateLimitExhaustedError is raised."""
    retrier = RateLimitRetrier(on_rate_limit=lambda _: None)
    for _ in range(10):
        retrier.handle(_rl_resp(retry_after="1"))
    with pytest.raises(RateLimitExhaustedError):
        retrier.handle(_rl_resp(retry_after="1"))


def test_reset_clears_retry_count() -> None:
    """Reset allows retries to start fresh."""
    retrier = RateLimitRetrier(on_rate_limit=lambda _: None)
    for _ in range(9):
        retrier.handle(_rl_resp(retry_after="1"))
    retrier.reset()
    wait = retrier.handle(_rl_resp(retry_after="5"))
    assert wait == 5  # Fresh first retry, not backoff


def test_notification_callback_called() -> None:
    """Notification callback invoked with wait time before each retry."""
    waits: list[int] = []
    retrier = RateLimitRetrier(on_rate_limit=waits.append)
    retrier.handle(_rl_resp(retry_after="15"))
    retrier.handle(_rl_resp(retry_after="20"))
    assert waits == [15, 30]  # first=15, second=max(20, 15*2)=30


def test_no_callback_when_no_retry() -> None:
    """Callback is not invoked when handle is not called."""
    waits: list[int] = []
    RateLimitRetrier(on_rate_limit=waits.append)
    assert waits == []
