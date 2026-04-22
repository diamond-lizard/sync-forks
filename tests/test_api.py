#!/usr/bin/env python3
"""Tests for sync_forks.api module."""
from __future__ import annotations

import shutil
import subprocess
from unittest.mock import MagicMock

import pytest
import requests
from helpers import make_response

from sync_forks.api import get_default_branch, merge_upstream
from sync_forks.errors import make_error_tracker
from sync_forks.retry import RateLimitRetrier
from sync_forks.session import create_session
from sync_forks.token import retrieve_token


def _has_pass() -> bool:
    """Check if pass and key are available."""
    if not shutil.which("pass"):
        return False
    r = subprocess.run(("pass", "show", "github.com/fgpat/contents-rw-and-workflows-rw"),
        capture_output=True, text=True, timeout=5)
    return r.returncode == 0 and bool(r.stdout.strip())


def _noop(_w: int) -> None:
    """No-op callback."""


_S = pytest.mark.skipif(not _has_pass(), reason="pass/key unavailable")


def _ctx() -> tuple[RateLimitRetrier, dict[str, int]]:
    """Create retrier and tracker."""
    return RateLimitRetrier(_noop), make_error_tracker()


@_S
def test_get_default_branch_real() -> None:
    """Real API call to known public repo returns default_branch."""
    s = create_session(retrieve_token())
    r, t = _ctx()
    result = get_default_branch(s, "octocat", "Hello-World", r, t)
    assert isinstance(result.branch, str) and len(result.branch) > 0


@_S
def test_get_nonexistent_repo(capsys: pytest.CaptureFixture[str]) -> None:
    """Real 404 returns None with auth note on stderr."""
    s = create_session(retrieve_token())
    r, t = _ctx()
    result = get_default_branch(s, "octocat", "no-such-repo-xyz-99", r, t)
    assert result.branch is None
    assert "404" in capsys.readouterr().err


def test_get_missing_default_branch(capsys: pytest.CaptureFixture[str]) -> None:
    """Constructed response missing default_branch is skipped."""
    session = MagicMock(spec=requests.Session)
    session.get.return_value = make_response(body=b'{"full_name": "o/r"}')
    r, t = _ctx()
    assert get_default_branch(session, "o", "r", r, t).branch is None
    assert "missing default_branch" in capsys.readouterr().err


def test_merge_upstream_success() -> None:
    """Constructed 200 response indicates successful merge."""
    session = MagicMock(spec=requests.Session)
    session.post.return_value = make_response(body=b'{"merge_type": "ff"}')
    r, t = _ctx()
    assert merge_upstream(session, "o", "r", "main", r, t).ok is True
    assert "merge-upstream" in session.post.call_args.args[0]


def test_merge_upstream_409_not_counted(capsys: pytest.CaptureFixture[str]) -> None:
    """409 Conflict reported but NOT counted toward threshold."""
    session = MagicMock(spec=requests.Session)
    resp = make_response(body=b'{"message": "Conflict"}')
    resp.status_code = 409
    session.post.return_value = resp
    r, t = _ctx()
    assert merge_upstream(session, "o", "r", "main", r, t).ok is False
    assert "409" in capsys.readouterr().err
    assert t.get("api.github.com", 0) == 0


def test_merge_upstream_422_reported(capsys: pytest.CaptureFixture[str]) -> None:
    """422 error is reported on stderr."""
    session = MagicMock(spec=requests.Session)
    resp = make_response(body=b'{"message": "Validation Failed"}')
    resp.status_code = 422
    session.post.return_value = resp
    r, t = _ctx()
    assert merge_upstream(session, "o", "r", "main", r, t).ok is False
    err = capsys.readouterr().err
    assert "422" in err
    assert "Validation Failed" in err
