#!/usr/bin/env python3
"""Structured error types and result containers for sync-forks."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests

from sync_forks.constants import MAX_RESPONSE_SIZE


@dataclass(frozen=True)
class SyncError:
    """A structured record of a single sync failure."""

    repo: str
    kind: str
    operation: str
    status_code: int | None = None
    api_message: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class ApiResult:
    """Result of execute_api_call: parsed data or structured error."""

    data: dict[str, object] | None
    error: SyncError | None


@dataclass(frozen=True)
class BranchResult:
    """Result of get_default_branch: branch name or structured error."""

    branch: str | None
    error: SyncError | None


@dataclass(frozen=True)
class MergeResult:
    """Result of merge_upstream: success flag or structured error."""

    ok: bool
    error: SyncError | None


def http_error(
    repo: str, operation: str, status_code: int, api_message: str | None,
) -> SyncError:
    """Create a SyncError for an HTTP error response."""
    return SyncError(
        repo=repo, kind="http", operation=operation,
        status_code=status_code, api_message=api_message,
    )


def network_error(repo: str, operation: str, exc: Exception) -> SyncError:
    """Create a SyncError for a network/connection failure."""
    return SyncError(
        repo=repo, kind="network", operation=operation,
        detail=f"{type(exc).__name__}: {exc}",
    )


def parse_error(repo: str, operation: str, detail: str) -> SyncError:
    """Create a SyncError for a response parsing failure."""
    return SyncError(
        repo=repo, kind="parse", operation=operation, detail=detail,
    )


def missing_field_error(repo: str, operation: str, field: str) -> SyncError:
    """Create a SyncError for a missing expected field in the response."""
    return SyncError(
        repo=repo, kind="missing_field", operation=operation,
        detail=f"missing {field} in response",
    )


def extract_api_message(
    response: requests.Response,
    pre_read_body: bytes | None = None,
) -> str | None:
    """Extract 'message' from an error response body, or None.

    Returns None for non-JSON, missing field, or oversized bodies.
    """
    raw = pre_read_body if pre_read_body is not None else response.content
    if len(raw) > MAX_RESPONSE_SIZE:
        return None
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    msg = obj.get("message") if isinstance(obj, dict) else None
    return (msg.strip() or None) if isinstance(msg, str) else None
