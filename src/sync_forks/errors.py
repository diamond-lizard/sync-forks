#!/usr/bin/env python3
"""Per-host error tracking with threshold-based abort."""
from __future__ import annotations

import sys

from sync_forks.constants import PER_HOST_ERROR_THRESHOLD


class HostErrorThresholdExceeded(Exception):
    """Raised when a host exceeds the per-host error threshold."""

    host: str
    count: int

    def __init__(self, host: str, count: int) -> None:
        """Store the offending host and its error count."""
        super().__init__(f"Host {host} exceeded error threshold ({count})")
        self.host = host
        self.count = count


def make_error_tracker() -> dict[str, int]:
    """Create a new per-host error counter."""
    return {}


def record_error(tracker: dict[str, int], host: str) -> None:
    """Record an error for a host; raise if threshold exceeded.

    Increments the error count for the given host. If the count
    reaches PER_HOST_ERROR_THRESHOLD, raises HostErrorThresholdExceeded.
    """
    tracker[host] = tracker.get(host, 0) + 1
    if tracker[host] >= PER_HOST_ERROR_THRESHOLD:
        raise HostErrorThresholdExceeded(host, tracker[host])



def classify_http_error(
    status_code: int, owner: str, repo: str,
    api_message: str | None = None,
) -> str:
    """Return a descriptive error message for an HTTP error status.

    Does not handle rate-limited responses (403/429 with rate limit
    indicators) — those are handled by ratelimit.py before reaching
    this function.
    """
    repo_id = f"{owner}/{repo}"
    if status_code == 404:
        return f"{repo_id}: 404 Not Found (repo may be private or token lacks access)"
    if status_code == 409:
        base = f"{repo_id}: 409 Conflict"
        return f"{base}: {api_message}" if api_message else base
    base = f"{repo_id}: HTTP {status_code}"
    return f"{base}: {api_message}" if api_message else base


def is_threshold_countable(status_code: int) -> bool:
    """Return whether an HTTP error counts toward per-host threshold.

    409 Conflict does not count. Rate-limited responses are handled
    separately and never reach this function.
    """
    return status_code != 409


def report_error(message: str) -> None:
    """Print an error message to stderr."""
    print(message, file=sys.stderr)


def classify_network_error(
    error: Exception, owner: str, repo: str,
) -> str:
    """Return a descriptive error message for a network/transient error.

    Covers timeout errors, connection failures, DNS resolution errors,
    and SSL errors.
    """
    repo_id = f"{owner}/{repo}"
    return f"{repo_id}: {type(error).__name__}: {error}"


def is_server_error(status_code: int) -> bool:
    """Return whether a status code is a 5xx server error."""
    return 500 <= status_code < 600
