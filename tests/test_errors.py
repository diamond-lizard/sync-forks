#!/usr/bin/env python3
"""Tests for per-host error tracking and error classification."""
from __future__ import annotations

import pytest

from sync_forks.errors import (
    HostErrorThresholdExceeded,
    classify_http_error,
    classify_network_error,
    is_threshold_countable,
    make_error_tracker,
    record_error,
    report_error,
)


def test_tracker_starts_at_zero() -> None:
    """New tracker has no entries."""
    tracker = make_error_tracker()
    assert tracker == {}


def test_record_error_increments() -> None:
    """Recording an error increments the count for that host."""
    tracker = make_error_tracker()
    record_error(tracker, "api.github.com")
    assert tracker["api.github.com"] == 1


def test_threshold_exceeded_after_five() -> None:
    """Threshold exceeded raises after 5 errors."""
    tracker = make_error_tracker()
    for _ in range(4):
        record_error(tracker, "api.github.com")
    with pytest.raises(HostErrorThresholdExceeded) as exc_info:
        record_error(tracker, "api.github.com")
    assert exc_info.value.host == "api.github.com"
    assert exc_info.value.count == 5


def test_threshold_not_exceeded_after_four() -> None:
    """Four errors does not trigger threshold."""
    tracker = make_error_tracker()
    for _ in range(4):
        record_error(tracker, "api.github.com")
    assert tracker["api.github.com"] == 4


def test_independent_host_tracking() -> None:
    """Errors from different hosts tracked independently."""
    tracker = make_error_tracker()
    for _ in range(4):
        record_error(tracker, "api.github.com")
    record_error(tracker, "other.host.com")
    assert tracker["api.github.com"] == 4
    assert tracker["other.host.com"] == 1


def test_threshold_countable_classification() -> None:
    """409 not countable; 404 and 500 are countable."""
    assert not is_threshold_countable(409)
    assert is_threshold_countable(404)
    assert is_threshold_countable(500)


def test_classify_404_includes_auth_note() -> None:
    """404 error message mentions possible auth issues."""
    msg = classify_http_error(404, "owner", "repo")
    assert "404" in msg
    assert "private" in msg or "token" in msg


def test_classify_409_conflict() -> None:
    """409 produces a conflict message."""
    msg = classify_http_error(409, "owner", "repo")
    assert "409" in msg
    assert "owner/repo" in msg


def test_classify_other_http() -> None:
    """Other HTTP codes produce a generic message."""
    msg = classify_http_error(422, "owner", "repo")
    assert "422" in msg
    assert "owner/repo" in msg


def test_classify_network_error() -> None:
    """Network error message includes type and details."""
    err = ConnectionError("Connection refused")
    msg = classify_network_error(err, "owner", "repo")
    assert "ConnectionError" in msg
    assert "owner/repo" in msg


def test_report_error_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """report_error prints to stderr."""
    report_error("something went wrong")
    assert "something went wrong" in capsys.readouterr().err
