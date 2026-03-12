#!/usr/bin/env python3
"""Tests for 5xx single-retry logic."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    import requests
from helpers import make_response

from sync_forks.retryable import retry_on_5xx


def _make_5xx() -> requests.Response:
    """Build a 500 response."""
    resp = make_response()
    resp.status_code = 500
    return resp


def _make_200() -> requests.Response:
    """Build a 200 response."""
    return make_response()


def _make_429() -> requests.Response:
    """Build a 429 rate-limited response."""
    resp = make_response()
    resp.status_code = 429
    resp.headers["x-ratelimit-remaining"] = "0"
    return resp


@patch("sync_forks.retryable.time.sleep")
def test_5xx_retry_success(mock_sleep: object) -> None:
    """5xx retried once; if retry returns 200, return success."""
    success = _make_200()
    result = retry_on_5xx(_make_5xx(), lambda: success)
    assert result.status_code == 200


@patch("sync_forks.retryable.time.sleep")
def test_5xx_retry_also_5xx(mock_sleep: object) -> None:
    """5xx retried once; if retry also 5xx, return retry response."""
    also_5xx = _make_5xx()
    result = retry_on_5xx(_make_5xx(), lambda: also_5xx)
    assert result.status_code == 500


@patch("sync_forks.retryable.time.sleep")
def test_5xx_retry_rate_limited(mock_sleep: object) -> None:
    """5xx retry that gets rate-limited returns 429 response."""
    rate_limited = _make_429()
    result = retry_on_5xx(_make_5xx(), lambda: rate_limited)
    assert result.status_code == 429


def test_non_5xx_not_retried() -> None:
    """Non-5xx response returned unchanged without retry."""
    called = False

    def should_not_call() -> requests.Response:
        nonlocal called
        called = True
        return _make_200()

    result = retry_on_5xx(_make_200(), should_not_call)
    assert result.status_code == 200
    assert not called
