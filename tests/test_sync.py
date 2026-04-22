#!/usr/bin/env python3
"""Tests for sync_forks.sync module."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from helpers import make_fork_entry

from sync_forks.sync import sync_repos
from sync_forks.sync_error import BranchResult, MergeResult


def _noop(_w: int) -> None:
    """No-op rate limit callback."""


def _session() -> MagicMock:
    """Create a mock session."""
    return MagicMock()


def _br(branch: str | None) -> BranchResult:
    """Create a BranchResult for testing."""
    return BranchResult(branch=branch, error=None)


def _mr(ok: bool) -> MergeResult:
    """Create a MergeResult for testing."""
    return MergeResult(ok=ok, error=None)


def test_empty_list_returns_empty_result() -> None:
    """Orchestration with empty behind-only list does nothing."""
    result = sync_repos([], _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == []
    assert result["failed"] == []
    assert result["errors"] == []


@patch("sync_forks.sync.merge_upstream", return_value=_mr(True))
@patch("sync_forks.sync.get_default_branch", return_value=_br("main"))
def test_sync_multiple_entries(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Orchestration iterates over entries and syncs them."""
    entries = [
        make_fork_entry("https://github.com/owner/repo1", 0, 3),
        make_fork_entry("https://github.com/owner/repo2", 0, 1),
    ]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == ["owner/repo1", "owner/repo2"]
    assert result["failed"] == []
    assert mock_branch.call_count == 2
    assert mock_merge.call_count == 2


@patch("sync_forks.sync.merge_upstream", return_value=_mr(True))
@patch("sync_forks.sync.get_default_branch", return_value=_br("main"))
def test_invalid_url_skipped(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Entries with invalid URLs are skipped."""
    entries = [
        make_fork_entry("not-a-url", 0, 1),
        make_fork_entry("https://github.com/owner/repo1", 0, 1),
    ]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == ["owner/repo1"]
    assert result["failed"] == []
    assert mock_branch.call_count == 1


@patch("sync_forks.sync.merge_upstream", return_value=_mr(False))
@patch("sync_forks.sync.get_default_branch", return_value=_br("main"))
def test_failed_merge_recorded(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Failed merge-upstream is recorded in failed list."""
    entries = [make_fork_entry("https://github.com/owner/repo1", 0, 1)]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == []
    assert result["failed"] == ["owner/repo1"]


@patch("sync_forks.sync.merge_upstream")
@patch("sync_forks.sync.get_default_branch", return_value=_br(None))
def test_no_branch_recorded_as_failed(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Failure to get default branch is recorded in failed list."""
    entries = [make_fork_entry("https://github.com/owner/repo1", 0, 1)]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["failed"] == ["owner/repo1"]
    mock_merge.assert_not_called()
