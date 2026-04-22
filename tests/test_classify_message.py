#!/usr/bin/env python3
"""Tests for classify_http_error with api_message parameter."""
from __future__ import annotations

from sync_forks.errors import classify_http_error


def test_422_with_message_includes_it() -> None:
    """422 with api_message appends the message to output."""
    msg = classify_http_error(422, "o", "r", api_message="workflow scope required")
    assert "422" in msg
    assert "workflow scope required" in msg
    assert "o/r" in msg


def test_422_without_message_keeps_current_format() -> None:
    """422 without api_message produces the generic HTTP format."""
    msg = classify_http_error(422, "o", "r")
    assert msg == "o/r: HTTP 422"


def test_409_with_message_includes_it() -> None:
    """409 with api_message appends the message after Conflict."""
    msg = classify_http_error(409, "o", "r", api_message="merge conflict details")
    assert "409 Conflict" in msg
    assert "merge conflict details" in msg


def test_404_ignores_api_message() -> None:
    """404 keeps custom hint and does NOT include api_message."""
    msg_with = classify_http_error(404, "o", "r", api_message="extra detail")
    msg_without = classify_http_error(404, "o", "r")
    assert "extra detail" not in msg_with
    assert msg_with == msg_without


def test_500_with_message_includes_it() -> None:
    """500 with api_message appends the message."""
    msg = classify_http_error(500, "o", "r", api_message="internal error")
    assert "500" in msg
    assert "internal error" in msg


def test_none_message_same_as_omitted() -> None:
    """Passing api_message=None gives same result as omitting it."""
    without = classify_http_error(422, "o", "r")
    with_none = classify_http_error(422, "o", "r", api_message=None)
    assert without == with_none
