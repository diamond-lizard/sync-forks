#!/usr/bin/env python3
"""Tests for sync_forks.input module."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from sync_forks.input import extract_fork_entries, parse_json, read_input, validate_structure


def test_read_input_from_file() -> None:
    """Reading from a file returns its content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"results": []}')
        path = f.name
    try:
        assert read_input(path) == '{"results": []}'
    finally:
        os.unlink(path)


def test_read_input_from_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reading from '-' reads stdin."""
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO('{"data": 1}'))
    assert read_input("-") == '{"data": 1}'


def test_read_input_missing_file() -> None:
    """Reading a nonexistent file exits with code 1."""
    with pytest.raises(SystemExit) as exc_info:
        read_input("/nonexistent/path/file.json")
    assert exc_info.value.code == 1


def test_parse_json_valid() -> None:
    """Valid JSON string is parsed correctly."""
    result = parse_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid JSON prints error to stderr and exits 1."""
    with pytest.raises(SystemExit) as exc_info:
        parse_json("{bad json")
    assert exc_info.value.code == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_validate_structure_valid() -> None:
    """Dict with 'results' list passes validation."""
    result = validate_structure({"results": [1, 2, 3]})
    assert result == [1, 2, 3]


def test_validate_structure_not_dict(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-dict root exits with code 1."""
    with pytest.raises(SystemExit) as exc_info:
        validate_structure([1, 2])
    assert exc_info.value.code == 1
    assert "object" in capsys.readouterr().err


def test_validate_structure_missing_results(capsys: pytest.CaptureFixture[str]) -> None:
    """Dict without 'results' exits with code 1."""
    with pytest.raises(SystemExit) as exc_info:
        validate_structure({"other": []})
    assert exc_info.value.code == 1
    assert "results" in capsys.readouterr().err


def test_validate_structure_results_not_list(capsys: pytest.CaptureFixture[str]) -> None:
    """Dict with non-list 'results' exits with code 1."""
    with pytest.raises(SystemExit) as exc_info:
        validate_structure({"results": "not a list"})
    assert exc_info.value.code == 1


def test_extract_with_sample_data() -> None:
    """Extraction works with realistic sample data."""
    with open("soma-init-repo-check-output.json") as f:
        data = json.load(f)
    results = validate_structure(data)
    forks = extract_fork_entries(results)
    assert len(forks) > 0
    for fork in forks:
        assert isinstance(fork["repo_url"], str)
        assert isinstance(fork["ahead_by"], int)
        assert isinstance(fork["behind_by"], int)
