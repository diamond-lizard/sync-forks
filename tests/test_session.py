#!/usr/bin/env python3
"""Tests for the session factory."""
from __future__ import annotations

from sync_forks.auth import GitHubAuth
from sync_forks.constants import REQUIRED_HEADERS
from sync_forks.session import create_session


def test_session_has_accept_header() -> None:
    """Session includes the required Accept header."""
    session = create_session("tok")
    assert session.headers["Accept"] == REQUIRED_HEADERS["Accept"]


def test_session_has_api_version_header() -> None:
    """Session includes the required X-GitHub-Api-Version header."""
    session = create_session("tok")
    expected = REQUIRED_HEADERS["X-GitHub-Api-Version"]
    assert session.headers["X-GitHub-Api-Version"] == expected


def test_session_has_user_agent_header() -> None:
    """Session includes the required User-Agent header."""
    session = create_session("tok")
    assert session.headers["User-Agent"] == REQUIRED_HEADERS["User-Agent"]


def test_session_has_auth_instance() -> None:
    """Session has a GitHubAuth instance set."""
    session = create_session("tok")
    assert isinstance(session.auth, GitHubAuth)


def test_headers_match_constants() -> None:
    """All required headers from constants are present on the session."""
    session = create_session("tok")
    for key, value in REQUIRED_HEADERS.items():
        assert session.headers[key] == value
