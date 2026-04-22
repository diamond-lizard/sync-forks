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
from sync_forks.sync_error import BranchResult, MergeResult, missing_field_error


def get_default_branch(
    session: requests.Session,
    owner: str,
    repo: str,
    retrier: RateLimitRetrier,
    error_tracker: dict[str, int],
) -> BranchResult:
    """Fetch the default branch name for a repository.

    Returns BranchResult with the branch name on success,
    or a structured error if the request failed.
    """
    url = build_repo_url(owner, repo)
    def make_request() -> requests.Response:
        return session.get(url, timeout=REQUEST_TIMEOUT)
    api_result = execute_api_call(
        make_request, NON_MUTATIVE_REQUEST_DELAY,
        retrier, error_tracker, owner, repo, "get_default_branch",
    )
    if api_result.data is None:
        return BranchResult(None, api_result.error)
    branch = api_result.data.get("default_branch")
    if not isinstance(branch, str):
        repo_id = f"{owner}/{repo}"
        report_error(f"{repo_id}: missing default_branch in response")
        err = missing_field_error(repo_id, "get_default_branch", "default_branch")
        return BranchResult(None, err)
    return BranchResult(branch, None)


def merge_upstream(
    session: requests.Session,
    owner: str,
    repo: str,
    branch: str,
    retrier: RateLimitRetrier,
    error_tracker: dict[str, int],
) -> MergeResult:
    """Sync a fork's branch with its upstream via merge-upstream API.

    Returns MergeResult with success flag and optional structured error.
    """
    url = build_repo_url(owner, repo) + "/merge-upstream"
    def make_request() -> requests.Response:
        return session.post(url, json={"branch": branch}, timeout=REQUEST_TIMEOUT)
    api_result = execute_api_call(
        make_request, MUTATIVE_REQUEST_DELAY,
        retrier, error_tracker, owner, repo, "merge_upstream",
    )
    if api_result.data is None:
        return MergeResult(False, api_result.error)
    return MergeResult(True, None)
