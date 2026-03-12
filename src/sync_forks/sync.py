#!/usr/bin/env python3
"""Sync orchestration loop for behind-only forks."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import requests

    from sync_forks.types import ForkEntry, SyncResult

from sync_forks.api import get_default_branch, merge_upstream
from sync_forks.errors import HostErrorThresholdExceeded, make_error_tracker
from sync_forks.output import print_sync_failed, print_synced
from sync_forks.retry import RateLimitExhaustedError, RateLimitRetrier
from sync_forks.url import parse_owner_repo


class SyncAbortError(Exception):
    """Wraps abort exceptions to carry partial SyncResult."""

    partial_result: SyncResult

    def __init__(self, partial_result: SyncResult, cause: BaseException) -> None:
        """Store partial result and chain the original cause."""
        super().__init__(str(cause))
        self.partial_result = partial_result
        self.__cause__ = cause



def _make_empty_result() -> SyncResult:
    """Create an empty SyncResult."""
    return {"synced": [], "failed": []}


def sync_repos(
    entries: list[ForkEntry],
    session: requests.Session,
    *,
    quiet: bool,
    on_rate_limit: Callable[[int], None],
) -> SyncResult:
    """Sync all behind-only forks, returning results.

    Iterates over entries, fetches default branch, calls
    merge-upstream, and accumulates synced/failed lists.
    """
    result = _make_empty_result()
    tracker = make_error_tracker()
    retrier = RateLimitRetrier(on_rate_limit)
    try:
        for entry in entries:
            _process_entry(entry, session, result, tracker, retrier, quiet=quiet)
    except HostErrorThresholdExceeded as exc:
        raise SyncAbortError(result, exc) from exc
    except RateLimitExhaustedError as exc:
        raise SyncAbortError(result, exc) from exc
    except KeyboardInterrupt as exc:
        raise SyncAbortError(result, exc) from exc
    return result


def _process_entry(
    entry: ForkEntry,
    session: requests.Session,
    result: SyncResult,
    tracker: dict[str, int],
    retrier: RateLimitRetrier,
    *,
    quiet: bool,
) -> None:
    """Process a single fork entry: parse URL, get branch, merge."""
    parsed = parse_owner_repo(entry["repo_url"])
    if not parsed:
        return
    owner, repo = parsed
    try:
        branch = get_default_branch(session, owner, repo, retrier, tracker)
        if branch is None:
            result["failed"].append(f"{owner}/{repo}")
            print_sync_failed(owner, repo, "could not get default branch", quiet=quiet)
            return
        if merge_upstream(session, owner, repo, branch, retrier, tracker):
            result["synced"].append(f"{owner}/{repo}")
            print_synced(owner, repo, quiet=quiet)
        else:
            result["failed"].append(f"{owner}/{repo}")
            print_sync_failed(owner, repo, "merge-upstream failed", quiet=quiet)
    except HostErrorThresholdExceeded:
        result["failed"].append(f"{owner}/{repo}")
        raise
