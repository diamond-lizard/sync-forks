#!/usr/bin/env python3
"""Sync orchestration loop for behind-only forks."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import requests

    from sync_forks.sync_error import SyncError
    from sync_forks.types import ForkEntry, SyncResult

from sync_forks.api import get_default_branch, merge_upstream
from sync_forks.errors import HostErrorThresholdExceeded, make_error_tracker
from sync_forks.exceptions import SyncAbortError
from sync_forks.output import print_sync_failed, print_synced, print_syncing
from sync_forks.retry import RateLimitExhaustedError, RateLimitRetrier
from sync_forks.url import parse_owner_repo


def _make_empty_result() -> SyncResult:
    """Create an empty SyncResult."""
    return {"synced": [], "failed": [], "errors": []}


def _record_failure(
    result: SyncResult, repo: str, error: SyncError | None,
) -> None:
    """Atomically append to both failed and errors lists."""
    result["failed"].append(repo)
    if error is not None:
        result["errors"].append(error)


def sync_repos(
    entries: list[ForkEntry],
    session: requests.Session,
    *,
    quiet: bool,
    on_rate_limit: Callable[[int], None],
) -> SyncResult:
    """Sync all behind-only forks, returning results.

    Iterates over entries, fetches default branch, calls
    merge-upstream, and accumulates synced/failed/errors lists.
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
    repo_id = f"{owner}/{repo}"
    print_syncing(owner, repo, quiet=quiet)
    try:
        br = get_default_branch(session, owner, repo, retrier, tracker)
        if br.branch is None:
            _record_failure(result, repo_id, br.error)
            print_sync_failed(owner, repo, "could not get default branch", quiet=quiet)
            return
        mr = merge_upstream(session, owner, repo, br.branch, retrier, tracker)
        if mr.ok:
            result["synced"].append(repo_id)
            print_synced(owner, repo, quiet=quiet)
        else:
            _record_failure(result, repo_id, mr.error)
            print_sync_failed(owner, repo, "merge-upstream failed", quiet=quiet)
    except HostErrorThresholdExceeded:
        _record_failure(result, repo_id, None)
        raise
