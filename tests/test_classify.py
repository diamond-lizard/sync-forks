#!/usr/bin/env python3
"""Tests for sync_forks.classify module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sync_forks.classify import classify_forks

if TYPE_CHECKING:
    from sync_forks.types import ForkEntry


def _entry(url: str, ahead: int, behind: int) -> ForkEntry:
    """Create a ForkEntry for testing."""
    return {"repo_url": url, "ahead_by": ahead, "behind_by": behind}


def test_all_behind_only() -> None:
    """All entries behind-only are returned in behind_only."""
    forks = [_entry("a", 0, 5), _entry("b", 0, 3)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 2
    assert len(result["ahead_and_behind"]) == 0


def test_all_ahead_and_behind() -> None:
    """All entries ahead-and-behind are returned in ahead_and_behind."""
    forks = [_entry("a", 2, 5), _entry("b", 1, 3)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 0
    assert len(result["ahead_and_behind"]) == 2


def test_mixed_list() -> None:
    """Mixed list is correctly separated."""
    forks = [_entry("a", 0, 5), _entry("b", 2, 3), _entry("c", 0, 1)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 2
    assert len(result["ahead_and_behind"]) == 1


def test_behind_by_zero_excluded() -> None:
    """Entries with behind_by == 0 are excluded from both lists."""
    forks = [_entry("a", 0, 0), _entry("b", 3, 0)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 0
    assert len(result["ahead_and_behind"]) == 0


def test_ahead_only_excluded() -> None:
    """Entry with ahead_by > 0 and behind_by == 0 is excluded."""
    forks = [_entry("a", 5, 0)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 0
    assert len(result["ahead_and_behind"]) == 0


def test_empty_input() -> None:
    """Empty input returns empty lists."""
    result = classify_forks([])
    assert result["behind_only"] == []
    assert result["ahead_and_behind"] == []


def test_behind_only_criteria() -> None:
    """Entry with ahead_by == 0 and behind_by > 0 goes to behind_only."""
    forks = [_entry("a", 0, 10)]
    result = classify_forks(forks)
    assert len(result["behind_only"]) == 1
    assert result["behind_only"][0]["repo_url"] == "a"
