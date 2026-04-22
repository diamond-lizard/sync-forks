#!/usr/bin/env python3
"""Tests for diagnostic hint output in the CLI context."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

from click.testing import CliRunner

from sync_forks.main import cli
from sync_forks.sync_error import SyncError

if TYPE_CHECKING:
    from pathlib import Path


def _input_json(count: int = 1) -> str:
    """Build minimal JSON input with behind-only forks."""
    entries = [
        {"status": "fork", "repo_url": f"https://github.com/o/r{i}",
         "ahead_by": 0, "behind_by": 1}
        for i in range(count)
    ]
    return json.dumps({"results": entries})


def _make_error(status: int, msg: str | None = None) -> SyncError:
    """Create a SyncError for testing."""
    return SyncError(
        repo="o/r0", kind="http", operation="merge_upstream",
        status_code=status, api_message=msg,
    )


def _run_with_result(
    result_dict: dict[str, object], tmp_path: Path, *, quiet: bool = False,
) -> object:
    """Run CLI with mocked sync_repos returning the given result."""
    p = tmp_path / "input.json"
    p.write_text(_input_json(1))
    args = ["--quiet", str(p)] if quiet else [str(p)]
    with (
        patch("sync_forks.token.retrieve_token", return_value="fake"),
        patch("sync_forks.session.create_session"),
        patch("sync_forks.sync.sync_repos", return_value=result_dict),
    ):
        return CliRunner().invoke(cli, args)


def test_diagnostics_printed_after_summary(tmp_path: Path) -> None:
    """Diagnostic hints appear in stderr after the summary line."""
    err = _make_error(422, "refusing without workflow scope")
    result = _run_with_result(
        {"synced": [], "failed": ["o/r0"], "errors": [err]}, tmp_path,
    )
    assert "Hint:" in result.stderr
    assert "Workflows" in result.stderr


def test_no_diagnostics_when_no_errors(tmp_path: Path) -> None:
    """No hints when there are no errors."""
    result = _run_with_result(
        {"synced": ["o/r0"], "failed": [], "errors": []}, tmp_path,
    )
    assert "Hint:" not in result.stderr


def test_diagnostics_shown_in_quiet_mode(tmp_path: Path) -> None:
    """Diagnostic hints appear even in quiet mode."""
    err = _make_error(401)
    result = _run_with_result(
        {"synced": [], "failed": ["o/r0"], "errors": [err]}, tmp_path,
        quiet=True,
    )
    assert "Hint:" in result.stderr
    assert "authentication" in result.stderr.lower()
