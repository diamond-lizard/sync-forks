#!/usr/bin/env python3
"""Tests for extract_api_message from request module."""
from __future__ import annotations

from helpers import make_response

from sync_forks.sync_error import extract_api_message


def test_valid_json_with_message() -> None:
    """JSON body with 'message' field returns the message string."""
    resp = make_response(body=b'{"message": "workflow scope required"}')
    assert extract_api_message(resp) == "workflow scope required"


def test_non_json_body_returns_none() -> None:
    """Non-JSON body returns None."""
    resp = make_response(body=b"<html>error</html>", content_type="text/html")
    assert extract_api_message(resp) is None


def test_json_missing_message_field() -> None:
    """JSON without 'message' key returns None."""
    resp = make_response(body=b'{"error": "something"}')
    assert extract_api_message(resp) is None


def test_pre_read_body_overrides_response() -> None:
    """When pre_read_body is provided, it is used instead of response body."""
    resp = make_response(body=b'{"message": "from response"}')
    pre = b'{"message": "from pre_read"}'
    assert extract_api_message(resp, pre_read_body=pre) == "from pre_read"


def test_empty_message_returns_none() -> None:
    """Empty string message returns None."""
    resp = make_response(body=b'{"message": ""}')
    assert extract_api_message(resp) is None


def test_whitespace_only_message_returns_none() -> None:
    """Whitespace-only message returns None."""
    resp = make_response(body=b'{"message": "   "}')
    assert extract_api_message(resp) is None


def test_non_string_message_returns_none() -> None:
    """Non-string message field returns None."""
    resp = make_response(body=b'{"message": 42}')
    assert extract_api_message(resp) is None


def test_message_is_stripped() -> None:
    """Leading/trailing whitespace is stripped from the message."""
    resp = make_response(body=b'{"message": "  trimmed  "}')
    assert extract_api_message(resp) == "trimmed"


def test_oversized_body_returns_none() -> None:
    """Body exceeding MAX_RESPONSE_SIZE returns None."""
    from sync_forks.constants import MAX_RESPONSE_SIZE

    huge = b'{"message": "' + b"x" * (MAX_RESPONSE_SIZE + 1) + b'"}'
    resp = make_response(body=huge)
    assert extract_api_message(resp) is None
