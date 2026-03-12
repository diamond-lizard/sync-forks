#!/usr/bin/env python3
"""Rate limit detection and wait time calculation for GitHub API."""
from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests

from sync_forks.constants import MAX_RESPONSE_SIZE


def _read_body_limited(response: requests.Response) -> bytes | None:
    """Read response body with size limit, returning None if exceeded."""
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=8192):
        total += len(chunk)
        if total > MAX_RESPONSE_SIZE:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _body_has_secondary_message(body: bytes) -> bool:
    """Check if parsed body contains a secondary rate limit message."""
    try:
        parsed: object = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(parsed, dict):
        return False
    message = parsed.get("message", "")
    if not isinstance(message, str):
        return False
    return "secondary rate limit" in message.lower()


class RateLimitVerdict:
    """Result of rate limit detection with optional pre-read body."""

    is_rate_limit: bool
    pre_read_body: bytes | None
    error: str | None

    def __init__(
        self,
        is_rate_limit: bool,
        pre_read_body: bytes | None = None,
        error: str | None = None,
    ) -> None:
        self.is_rate_limit = is_rate_limit
        self.pre_read_body = pre_read_body
        self.error = error


def detect_rate_limit(response: requests.Response) -> RateLimitVerdict:
    """Detect whether a 403/429 response is a rate limit.

    Returns a RateLimitVerdict indicating whether this is a rate limit,
    and for genuine 403/429s, includes the pre-read body bytes so the
    caller can pass them to the response processing pipeline.
    """
    remaining = response.headers.get("x-ratelimit-remaining")
    if remaining == "0":
        return RateLimitVerdict(is_rate_limit=True)
    body = _read_body_limited(response)
    if body is None:
        return RateLimitVerdict(
            is_rate_limit=False,
            error="Response body exceeded size limit during rate limit check",
        )
    if _body_has_secondary_message(body):
        return RateLimitVerdict(is_rate_limit=True, pre_read_body=body)
    return RateLimitVerdict(is_rate_limit=False, pre_read_body=body)


def calculate_wait_time(response: requests.Response) -> int:
    """Calculate how long to wait before retrying a rate-limited request.

    Priority: (1) x-ratelimit-reset header, (2) retry-after header,
    (3) default 60 seconds.
    """
    remaining = response.headers.get("x-ratelimit-remaining")
    reset_str = response.headers.get("x-ratelimit-reset")
    if remaining == "0" and reset_str is not None:
        try:
            reset_time = int(reset_str)
            return max(reset_time - int(time.time()), 1)
        except ValueError:
            pass
    retry_after = response.headers.get("retry-after")
    if retry_after is not None:
        try:
            return max(int(retry_after), 1)
        except ValueError:
            pass
    return 60
