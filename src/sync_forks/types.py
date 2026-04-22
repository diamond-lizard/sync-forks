#!/usr/bin/env python3
"""TypedDict definitions for structured data used across sync-forks."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from sync_forks.sync_error import SyncError


class ForkEntry(TypedDict):
    """A single fork entry from the input JSON."""

    repo_url: str
    ahead_by: int
    behind_by: int


class ClassifiedForks(TypedDict):
    """Forks classified by sync status."""

    behind_only: list[ForkEntry]
    ahead_and_behind: list[ForkEntry]


class SyncResult(TypedDict):
    """Results of the sync operation."""

    synced: list[str]
    failed: list[str]
    errors: list[SyncError]
