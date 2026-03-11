#!/usr/bin/env python3
"""Tests for sync_forks.input fork entry extraction."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from sync_forks.input import extract_fork_entries


def test_extract_fork_entries_valid() -> None:
    """Valid fork entries are extracted correctly."""
    results: list[object] = [
        {"status": "fork", "repo_url": "https://github.com/a/b", "ahead_by": 0, "behind_by": 5},
        {"status": "fork", "repo_url": "https://github.com/c/d", "ahead_by": 2, "behind_by": 3},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 2
    assert forks[0]["repo_url"] == "https://github.com/a/b"
    assert forks[1]["ahead_by"] == 2


def test_extract_fork_entries_mixed_statuses() -> None:
    """Non-fork entries are ignored."""
    results: list[object] = [
        {"status": "skipped:not_a_fork", "repo_url": "https://github.com/a/b"},
        {"status": "fork", "repo_url": "https://github.com/c/d", "ahead_by": 0, "behind_by": 1},
        {"status": "skipped:no_repo_directive", "repo_url": "https://github.com/e/f"},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 1
    assert forks[0]["repo_url"] == "https://github.com/c/d"


def test_extract_fork_entries_missing_repo_url(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry missing repo_url is skipped with warning."""
    results: list[object] = [{"status": "fork", "ahead_by": 0, "behind_by": 1}]
    forks = extract_fork_entries(results)
    assert len(forks) == 0
    assert "repo_url" in capsys.readouterr().err


def test_extract_fork_entries_missing_ahead_by(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry missing ahead_by is skipped with warning."""
    results: list[object] = [
        {"status": "fork", "repo_url": "https://github.com/a/b", "behind_by": 1},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 0
    assert "ahead_by" in capsys.readouterr().err


def test_extract_fork_entries_missing_behind_by(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry missing behind_by is skipped with warning."""
    results: list[object] = [
        {"status": "fork", "repo_url": "https://github.com/a/b", "ahead_by": 0},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 0
    assert "behind_by" in capsys.readouterr().err


def test_extract_fork_entries_non_integer_ahead_by(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry with non-integer ahead_by is skipped."""
    results: list[object] = [
        {"status": "fork", "repo_url": "https://github.com/a/b",
            "ahead_by": "five", "behind_by": 1},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 0


def test_extract_fork_entries_non_string_repo_url(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry with non-string repo_url is skipped."""
    results: list[object] = [
        {"status": "fork", "repo_url": 123, "ahead_by": 0, "behind_by": 1},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 0


def test_extract_fork_entries_empty_results() -> None:
    """Empty results list returns empty list."""
    assert extract_fork_entries([]) == []


def test_extract_fork_entries_boolean_ahead_by(capsys: pytest.CaptureFixture[str]) -> None:
    """Fork entry with boolean ahead_by is skipped (bool is subclass of int)."""
    results: list[object] = [
        {"status": "fork", "repo_url": "https://github.com/a/b", "ahead_by": True, "behind_by": 1},
    ]
    forks = extract_fork_entries(results)
    assert len(forks) == 0
