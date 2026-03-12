#!/usr/bin/env python3
"""Tests for rate limit detection and wait time calculation."""
from __future__ import annotations

import json
import time

from helpers import make_response

from sync_forks.ratelimit import calculate_wait_time, detect_rate_limit


def _rl_resp(
    status: int = 429, remaining: str | None = None, body: bytes = b"{}",
) -> object:
    """Build a response with rate limit headers."""
    resp = make_response(body=body)
    resp.status_code = status
    if remaining is not None:
        resp.headers["x-ratelimit-remaining"] = remaining
    return resp


def test_403_remaining_zero_is_rate_limit() -> None:
    """403 with x-ratelimit-remaining: 0 detected as rate limit."""
    verdict = detect_rate_limit(_rl_resp(status=403, remaining="0"))
    assert verdict.is_rate_limit is True


def test_429_remaining_zero_is_rate_limit() -> None:
    """429 with x-ratelimit-remaining: 0 detected as rate limit."""
    verdict = detect_rate_limit(_rl_resp(status=429, remaining="0"))
    assert verdict.is_rate_limit is True


def test_secondary_rate_limit_in_body() -> None:
    """403 with secondary rate limit message in body is rate limited."""
    body = json.dumps({"message": "secondary rate limit hit"}).encode()
    verdict = detect_rate_limit(_rl_resp(403, remaining="5", body=body))
    assert verdict.is_rate_limit is True
    assert verdict.pre_read_body == body


def test_genuine_403_not_rate_limit() -> None:
    """403 without rate limit indicators is genuine, returns pre-read body."""
    body = json.dumps({"message": "forbidden"}).encode()
    verdict = detect_rate_limit(_rl_resp(403, remaining="5", body=body))
    assert verdict.is_rate_limit is False
    assert verdict.pre_read_body == body


def test_oversize_body_not_rate_limit() -> None:
    """Body exceeding 10MB during secondary check is not a rate limit."""
    big = b"x" * (10 * 1024 * 1024 + 1)
    verdict = detect_rate_limit(_rl_resp(403, remaining="5", body=big))
    assert verdict.is_rate_limit is False
    assert verdict.error is not None


def test_wait_from_reset_header() -> None:
    """Wait time calculated from x-ratelimit-reset header."""
    future = int(time.time()) + 120
    resp = make_response()
    resp.headers["x-ratelimit-remaining"] = "0"
    resp.headers["x-ratelimit-reset"] = str(future)
    assert 118 <= calculate_wait_time(resp) <= 122


def test_wait_from_retry_after() -> None:
    """Wait time from retry-after when remaining is not 0."""
    resp = make_response()
    resp.headers["x-ratelimit-remaining"] = "5"
    resp.headers["retry-after"] = "30"
    assert calculate_wait_time(resp) == 30


def test_wait_default_60s() -> None:
    """Default 60s when no relevant headers present."""
    assert calculate_wait_time(make_response()) == 60


def test_wait_max_prevents_negative() -> None:
    """max(..., 1) prevents non-positive wait from clock skew."""
    resp = make_response()
    resp.headers["x-ratelimit-remaining"] = "0"
    resp.headers["x-ratelimit-reset"] = str(int(time.time()) - 100)
    assert calculate_wait_time(resp) == 1
