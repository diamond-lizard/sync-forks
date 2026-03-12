#!/usr/bin/env python3
"""Tests for sync_forks.sync module."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from helpers import make_fork_entry

from sync_forks.sync import sync_repos


def _noop(_w: int) -> None:
    """No-op rate limit callback."""


def _session() -> MagicMock:
    """Create a mock session."""
    return MagicMock()


def test_empty_list_returns_empty_result() -> None:
    """Orchestration with empty behind-only list does nothing."""
    result = sync_repos([], _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == []
    assert result["failed"] == []


@patch("sync_forks.sync.merge_upstream", return_value=True)
@patch("sync_forks.sync.get_default_branch", return_value="main")
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


@patch("sync_forks.sync.merge_upstream", return_value=True)
@patch("sync_forks.sync.get_default_branch", return_value="main")
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


@patch("sync_forks.sync.merge_upstream", return_value=False)
@patch("sync_forks.sync.get_default_branch", return_value="main")
def test_failed_merge_recorded(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Failed merge-upstream is recorded in failed list."""
    entries = [make_fork_entry("https://github.com/owner/repo1", 0, 1)]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["synced"] == []
    assert result["failed"] == ["owner/repo1"]


@patch("sync_forks.sync.merge_upstream")
@patch("sync_forks.sync.get_default_branch", return_value=None)
def test_no_branch_recorded_as_failed(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """Failure to get default branch is recorded in failed list."""
    entries = [make_fork_entry("https://github.com/owner/repo1", 0, 1)]
    result = sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert result["failed"] == ["owner/repo1"]
    mock_merge.assert_not_called()
