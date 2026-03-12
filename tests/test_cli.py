#!/usr/bin/env python3
"""Tests for the sync-forks CLI command."""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from sync_forks.main import cli

SAMPLE_FILE = str(Path(__file__).resolve().parent.parent / "soma-init-repo-check-output.json")


def _make_input(behind: int = 1, ahead_behind: int = 0) -> str:
    """Build minimal JSON input with the given fork counts."""
    entries = [{"status": "fork", "repo_url": f"https://github.com/o/b{i}",
        "ahead_by": 0, "behind_by": 1} for i in range(behind)]
    entries += [{"status": "fork", "repo_url": f"https://github.com/o/ab{i}",
        "ahead_by": 1, "behind_by": 1} for i in range(ahead_behind)]
    return json.dumps({"results": entries})


def test_help_flag() -> None:
    """--help outputs help text and exits 0."""
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "FILENAME" in result.output


def test_no_arguments_exits_2() -> None:
    """No arguments exits with code 2 (usage error)."""
    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 2


def test_dry_run_with_file(tmp_path: Path) -> None:
    """--dry-run with valid input prints report to stderr and exits 0."""
    p = tmp_path / "input.json"
    p.write_text(_make_input(behind=2, ahead_behind=1))
    result = CliRunner().invoke(cli, ["--dry-run", str(p)])
    assert result.exit_code == 0
    assert "Would sync o/b0" in result.stderr
    assert "Would sync o/b1" in result.stderr
    assert "Skipped o/ab0" in result.stderr


def test_dry_run_stdin() -> None:
    """--dry-run with - reads from stdin."""
    data = _make_input(behind=1)
    result = CliRunner().invoke(cli, ["--dry-run", "-"], input=data)
    assert result.exit_code == 0
    assert "Would sync o/b0" in result.stderr


def test_quiet_suppresses_dry_run_output(tmp_path: Path) -> None:
    """--quiet suppresses informational output in dry-run mode."""
    p = tmp_path / "input.json"
    p.write_text(_make_input(behind=2))
    result = CliRunner().invoke(
        cli, ["--dry-run", "--quiet", str(p)],
    )
    assert result.exit_code == 0
    assert result.stderr == ""


def test_invalid_json_exits_1(tmp_path: Path) -> None:
    """Invalid JSON input exits with code 1 and prints error to stderr."""
    p = tmp_path / "bad.json"
    p.write_text("not json {{{")
    result = CliRunner().invoke(cli, [str(p)])
    assert result.exit_code == 1
    assert "invalid JSON" in result.stderr


def test_nonexistent_file_exits_nonzero() -> None:
    """Non-existent input file exits with non-zero code and error message."""
    result = CliRunner().invoke(cli, ["/no/such/file.json"])
    assert result.exit_code != 0
    assert result.stderr != ""


def test_all_up_to_date_exits_0(tmp_path: Path) -> None:
    """Input with no behind forks prints message and exits 0."""
    p = tmp_path / "input.json"
    p.write_text(_make_input(behind=0, ahead_behind=0))
    result = CliRunner().invoke(cli, [str(p)])
    assert result.exit_code == 0
    assert "up to date" in result.stderr


def test_dry_run_sample_file() -> None:
    """--dry-run with the real sample file exits 0."""
    result = CliRunner().invoke(
        cli, ["--dry-run", SAMPLE_FILE],
    )
    assert result.exit_code == 0
    assert "Would sync" in result.stderr
