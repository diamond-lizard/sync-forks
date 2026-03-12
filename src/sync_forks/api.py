#!/usr/bin/env python3
"""GitHub API operations for sync-forks."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests

    from sync_forks.retry import RateLimitRetrier

from sync_forks.constants import (
    MUTATIVE_REQUEST_DELAY,
    NON_MUTATIVE_REQUEST_DELAY,
    REQUEST_TIMEOUT,
)
from sync_forks.errors import report_error
from sync_forks.request import build_repo_url, execute_api_call


def get_default_branch(
    session: requests.Session,
    owner: str,
    repo: str,
    retrier: RateLimitRetrier,
    error_tracker: dict[str, int],
) -> str | None:
    """Fetch the default branch name for a repository.

    Returns the branch name on success, or None if the repo should
    be skipped (error reported on stderr).
    """
    url = build_repo_url(owner, repo)
    def make_request() -> requests.Response:
        return session.get(url, timeout=REQUEST_TIMEOUT)
    result = execute_api_call(
        make_request, NON_MUTATIVE_REQUEST_DELAY,
        retrier, error_tracker, owner, repo,
    )
    if result is None:
        return None
    branch = result.get("default_branch")
    if not isinstance(branch, str):
        report_error(f"{owner}/{repo}: missing default_branch in response")
        return None
    return branch


def merge_upstream(
    session: requests.Session,
    owner: str,
    repo: str,
    branch: str,
    retrier: RateLimitRetrier,
    error_tracker: dict[str, int],
) -> bool:
    """Sync a fork's branch with its upstream via merge-upstream API.

    Returns True on success, False on failure (error reported on stderr).
    """
    url = build_repo_url(owner, repo) + "/merge-upstream"
    def make_request() -> requests.Response:
        return session.post(url, json={"branch": branch}, timeout=REQUEST_TIMEOUT)
    result = execute_api_call(
        make_request, MUTATIVE_REQUEST_DELAY,
        retrier, error_tracker, owner, repo,
    )
    return result is not None
