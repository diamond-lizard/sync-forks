#!/usr/bin/env python3
"""Tests for sync_forks.token module."""
from __future__ import annotations

import shutil
import subprocess
from unittest.mock import patch

import pytest

from sync_forks.token import retrieve_token

_PATCH = "sync_forks.token.subprocess.run"


def _pass_key_exists() -> bool:
    """Check whether the specific pass key exists."""
    if not shutil.which("pass"):
        return False
    r = subprocess.run(
        ("pass", "show", "github.com/fgpat/contents-rw-and-workflows-rw"),
        capture_output=True, text=True, timeout=5,
    )
    return r.returncode == 0 and bool(r.stdout.strip())


@pytest.mark.skipif(not _pass_key_exists(), reason="pass or key unavailable")
def test_retrieve_token_real() -> None:
    """Successful token retrieval using real pass."""
    token = retrieve_token()
    assert isinstance(token, str)
    assert len(token) > 0
    assert "\n" not in token


def test_pass_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    """pass not found on PATH exits with code 1."""
    with patch(_PATCH, side_effect=FileNotFoundError), pytest.raises(SystemExit) as exc_info:
        retrieve_token()
    assert exc_info.value.code == 1
    assert "'pass' not found" in capsys.readouterr().err


def test_pass_nonzero_exit(capsys: pytest.CaptureFixture[str]) -> None:
    """pass returns non-zero exit code exits with code 1."""
    rv = subprocess.CompletedProcess(
        args=("pass",), returncode=1, stdout="", stderr="key not found",
    )
    with patch(_PATCH, return_value=rv), pytest.raises(SystemExit) as exc_info:
        retrieve_token()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "exited with code 1" in err
    assert "key not found" in err


def test_pass_timeout(capsys: pytest.CaptureFixture[str]) -> None:
    """pass timeout exits with code 1."""
    exc = subprocess.TimeoutExpired(cmd="pass", timeout=30)
    with patch(_PATCH, side_effect=exc), pytest.raises(SystemExit) as exc_info:
        retrieve_token()
    assert exc_info.value.code == 1
    assert "timed out" in capsys.readouterr().err


def test_pass_empty_output(capsys: pytest.CaptureFixture[str]) -> None:
    """pass returns empty output exits with code 1."""
    rv = subprocess.CompletedProcess(args=("pass",), returncode=0, stdout="", stderr="")
    with patch(_PATCH, return_value=rv), pytest.raises(SystemExit) as exc_info:
        retrieve_token()
    assert exc_info.value.code == 1
    assert "empty output" in capsys.readouterr().err


def test_pass_whitespace_only(capsys: pytest.CaptureFixture[str]) -> None:
    """pass returns whitespace-only output exits with code 1."""
    rv = subprocess.CompletedProcess(args=("pass",), returncode=0, stdout="  \n\n", stderr="")
    with patch(_PATCH, return_value=rv), pytest.raises(SystemExit) as exc_info:
        retrieve_token()
    assert exc_info.value.code == 1
    assert "empty output" in capsys.readouterr().err


def test_pass_multiline_uses_first_line() -> None:
    """Token is extracted from first line of multi-line output."""
    rv = subprocess.CompletedProcess(
        args=("pass",), returncode=0,
        stdout="ghp_token123\nsome metadata\n", stderr="",
    )
    with patch(_PATCH, return_value=rv):
        assert retrieve_token() == "ghp_token123"
