#!/usr/bin/env python3
"""Output and summary formatting for sync-forks.

All output goes to stderr. Informational messages are suppressed
when quiet mode is enabled; errors and abort messages are always shown.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

from sync_forks.url import parse_owner_repo

if TYPE_CHECKING:
    from sync_forks.types import ForkEntry, SyncResult


def print_syncing(owner: str, repo: str, *, quiet: bool) -> None:
    """Print a message indicating a repo sync has started."""
    if not quiet:
        print(f"Syncing {owner}/{repo}...", file=sys.stderr)


def print_synced(owner: str, repo: str, *, quiet: bool) -> None:
    """Print a message indicating a repo was successfully synced."""
    if not quiet:
        print(f"Synced {owner}/{repo}.", file=sys.stderr)


def print_sync_failed(owner: str, repo: str, reason: str, *, quiet: bool) -> None:
    """Print a message indicating a repo sync failed."""
    if not quiet:
        print(f"Failed {owner}/{repo}: {reason}", file=sys.stderr)


def print_skipped(owner: str, repo: str, *, quiet: bool) -> None:
    """Print a message indicating a repo was skipped (ahead and behind)."""
    if not quiet:
        print(f"Skipped {owner}/{repo} (ahead and behind).", file=sys.stderr)


def print_dry_run_would_sync(owner: str, repo: str, *, quiet: bool) -> None:
    """Print a message indicating a repo would be synced in a real run."""
    if not quiet:
        print(f"Would sync {owner}/{repo}.", file=sys.stderr)


def print_ahead_and_behind_report(
    entries: list[ForkEntry], *, quiet: bool,
) -> None:
    """List all ahead-and-behind repos on stderr."""
    if quiet:
        return
    for entry in entries:
        parsed = parse_owner_repo(entry["repo_url"])
        if parsed:
            print_skipped(parsed[0], parsed[1], quiet=quiet)


def print_summary(
    result: SyncResult,
    ahead_and_behind: list[ForkEntry],
    *,
    quiet: bool,
) -> None:
    """Print the final summary line to stderr."""
    if quiet:
        return
    parts: list[str] = []
    if result["synced"]:
        parts.append(f"Synced {len(result['synced'])} repos")
    if ahead_and_behind:
        parts.append(f"skipped {len(ahead_and_behind)} (ahead-and-behind)")
    if result["failed"]:
        parts.append(f"{len(result['failed'])} errors")
    if not parts:
        parts.append("Nothing to do")
    print(", ".join(parts) + ".", file=sys.stderr)


def make_rate_limit_notifier(*, quiet: bool) -> Callable[[int], None]:
    """Return a callback that prints rate limit wait notifications.

    The returned function is passed as the on_rate_limit callback
    to retry.py. It accepts the wait time in seconds.
    """
    def notify(wait_seconds: int) -> None:
        if not quiet:
            msg = f"Rate limited. Waiting {wait_seconds}s before retrying..."
            print(msg, file=sys.stderr)
    return notify
