#!/usr/bin/env python3
"""Tests for sync_forks.sync abort handling."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from helpers import make_fork_entry

from sync_forks.errors import HostErrorThresholdExceeded
from sync_forks.retry import RateLimitExhaustedError
from sync_forks.sync import SyncAbortError, sync_repos


def _noop(_w: int) -> None:
    """No-op rate limit callback."""


def _session() -> MagicMock:
    """Create a mock session."""
    return MagicMock()


@patch("sync_forks.sync.merge_upstream", return_value=True)
@patch("sync_forks.sync.get_default_branch")
def test_host_error_threshold_aborts(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """After 5 errors, loop stops and SyncAbortError is raised."""
    mock_branch.side_effect = [
        "main",
        HostErrorThresholdExceeded("api.github.com", 5),
    ]
    entries = [
        make_fork_entry("https://github.com/owner/repo1", 0, 1),
        make_fork_entry("https://github.com/owner/repo2", 0, 1),
    ]
    with pytest.raises(SyncAbortError) as exc_info:
        sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert exc_info.value.partial_result["synced"] == ["owner/repo1"]
    assert isinstance(exc_info.value.__cause__, HostErrorThresholdExceeded)


@patch("sync_forks.sync.merge_upstream")
@patch("sync_forks.sync.get_default_branch")
def test_rate_limit_exhaustion_aborts(mock_branch: MagicMock, mock_merge: MagicMock) -> None:
    """RateLimitExhaustedError propagates as SyncAbortError."""
    mock_branch.side_effect = RateLimitExhaustedError("exhausted")
    entries = [make_fork_entry("https://github.com/owner/repo1", 0, 1)]
    with pytest.raises(SyncAbortError) as exc_info:
        sync_repos(entries, _session(), quiet=False, on_rate_limit=_noop)
    assert exc_info.value.partial_result["synced"] == []
    assert isinstance(exc_info.value.__cause__, RateLimitExhaustedError)
