#!/usr/bin/env python3
"""Tests for the GitHubAuth AuthBase subclass."""
from __future__ import annotations

import requests

from sync_forks.auth import GitHubAuth


def test_adds_auth_header_for_github_api() -> None:
    """Authorization header is added for api.github.com requests."""
    auth = GitHubAuth("test-token-123")
    req = requests.Request("GET", "https://api.github.com/repos/owner/repo")
    prepared = req.prepare()
    result = auth(prepared)
    assert result.headers["Authorization"] == "Bearer test-token-123"


def test_no_auth_header_for_other_hosts() -> None:
    """Authorization header is not added for non-GitHub hosts."""
    auth = GitHubAuth("test-token-123")
    req = requests.Request("GET", "https://example.com/some/path")
    prepared = req.prepare()
    result = auth(prepared)
    assert "Authorization" not in result.headers


def test_bearer_format() -> None:
    """Authorization header uses correct Bearer format."""
    auth = GitHubAuth("ghp_abc123")
    req = requests.Request("GET", "https://api.github.com/user")
    prepared = req.prepare()
    result = auth(prepared)
    assert result.headers["Authorization"] == "Bearer ghp_abc123"
