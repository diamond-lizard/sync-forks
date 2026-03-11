#!/usr/bin/env python3
"""Tests for sync_forks.url module."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from sync_forks.url import parse_owner_repo


def test_valid_github_url() -> None:
    """Valid HTTPS GitHub URL returns (owner, repo)."""
    result = parse_owner_repo("https://github.com/octocat/Hello-World")
    assert result == ("octocat", "Hello-World")


def test_trailing_slash() -> None:
    """URL with trailing slash works."""
    result = parse_owner_repo("https://github.com/octocat/Hello-World/")
    assert result == ("octocat", "Hello-World")


def test_too_many_path_components(capsys: pytest.CaptureFixture[str]) -> None:
    """URL with more than two path components is rejected."""
    result = parse_owner_repo("https://github.com/a/b/c")
    assert result is None
    assert "expected owner/repo" in capsys.readouterr().err


def test_too_few_path_components(capsys: pytest.CaptureFixture[str]) -> None:
    """URL with fewer than two path components is rejected."""
    result = parse_owner_repo("https://github.com/onlyowner")
    assert result is None
    assert "expected owner/repo" in capsys.readouterr().err


def test_empty_path(capsys: pytest.CaptureFixture[str]) -> None:
    """URL with empty path is rejected."""
    result = parse_owner_repo("https://github.com/")
    assert result is None
    assert "expected owner/repo" in capsys.readouterr().err


def test_owner_with_invalid_chars(capsys: pytest.CaptureFixture[str]) -> None:
    """Owner with whitespace or control characters is rejected."""
    result = parse_owner_repo("https://github.com/bad owner/repo")
    assert result is None
    assert "invalid owner" in capsys.readouterr().err


def test_repo_with_invalid_chars(capsys: pytest.CaptureFixture[str]) -> None:
    """Repo with invalid characters is rejected."""
    result = parse_owner_repo("https://github.com/owner/bad@repo!")
    assert result is None
    assert "invalid repo" in capsys.readouterr().err


def test_allowed_special_chars() -> None:
    """Owner/repo with hyphens, dots, and underscores pass."""
    result = parse_owner_repo("https://github.com/my-org.name/my_repo.py")
    assert result == ("my-org.name", "my_repo.py")


def test_non_https_url() -> None:
    """Non-HTTPS URL with valid path still parses (URL scheme not restricted)."""
    result = parse_owner_repo("http://github.com/owner/repo")
    assert result == ("owner", "repo")


def test_git_suffix() -> None:
    """URL with .git suffix — .git is part of the repo name."""
    result = parse_owner_repo("https://github.com/owner/repo.git")
    assert result == ("owner", "repo.git")


def test_path_only() -> None:
    """Bare path without scheme parses as path."""
    result = parse_owner_repo("owner/repo")
    assert result == ("owner", "repo")
