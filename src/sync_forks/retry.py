#!/usr/bin/env python3
"""Tenacity-based retry logic for rate-limited GitHub API requests."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import requests

from sync_forks.constants import MAX_RATE_LIMIT_RETRIES
from sync_forks.ratelimit import calculate_wait_time, detect_rate_limit


class RateLimitExhaustedError(Exception):
    """Raised when rate limit retries are exhausted."""


def is_rate_limited(response: requests.Response) -> bool:
    """Check if a response is rate-limited (403/429 with rate limit indicators)."""
    if response.status_code not in (403, 429):
        return False
    verdict = detect_rate_limit(response)
    return verdict.is_rate_limit


class RateLimitRetrier:
    """Manages rate limit retry state for a single API request.

    Tracks consecutive retries and applies exponential backoff using
    the greater of header-suggested wait and doubled previous wait.
    """

    _last_wait: int
    _retries: int
    _on_rate_limit: Callable[[int], None]

    def __init__(self, on_rate_limit: Callable[[int], None]) -> None:
        """Set up retry state."""
        self._last_wait = 0
        self._retries = 0
        self._on_rate_limit = on_rate_limit

    def handle(self, response: requests.Response) -> int:
        """Determine wait time for a rate-limited response.

        Returns the number of seconds to wait. Raises
        RateLimitExhaustedError after MAX_RATE_LIMIT_RETRIES.
        """
        self._retries += 1
        if self._retries > MAX_RATE_LIMIT_RETRIES:
            msg = "Rate limit retries exhausted"
            raise RateLimitExhaustedError(msg)
        header_wait = calculate_wait_time(response)
        if self._retries == 1:
            wait = header_wait
        else:
            backoff = self._last_wait * 2
            wait = max(header_wait, backoff)
        self._last_wait = wait
        self._on_rate_limit(wait)
        return wait

    def reset(self) -> None:
        """Reset retry counter after a successful request."""
        self._last_wait = 0
        self._retries = 0
