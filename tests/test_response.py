#!/usr/bin/env python3
"""Tests for the response processing pipeline."""
from __future__ import annotations

from helpers import make_response

from sync_forks.constants import MAX_RESPONSE_SIZE
from sync_forks.response import (
    check_content_length,
    check_content_type,
    process_response,
    read_body_streaming,
)


def test_valid_json_response() -> None:
    """Valid JSON response with correct Content-Type returns parsed data."""
    resp = make_response(b'{"key": "value"}', "application/json", "16")
    result = process_response(resp)
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_non_json_content_type_rejected() -> None:
    """Response with non-JSON Content-Type is rejected before reading body."""
    resp = make_response(b"<html></html>", "text/html")
    result = check_content_type(resp)
    assert result is not None
    assert "text/html" in result


def test_content_length_over_limit_rejected() -> None:
    """Response with Content-Length > 10MB is rejected before reading body."""
    big = str(MAX_RESPONSE_SIZE + 1)
    resp = make_response(content_length=big)
    result = check_content_length(resp)
    assert result is not None
    assert "too large" in result.lower()


def test_github_content_type_succeeds() -> None:
    """application/vnd.github+json (contains 'json') succeeds."""
    resp = make_response(b'{"ok": true}', "application/vnd.github+json")
    result = process_response(resp)
    assert isinstance(result, dict)


def test_streaming_body_exceeds_limit() -> None:
    """Body exceeding 10MB during streaming is aborted at the size limit."""
    big_body = b"x" * (MAX_RESPONSE_SIZE + 1)
    resp = make_response(big_body, "application/json")
    result = read_body_streaming(resp)
    assert isinstance(result, str)
    assert "exceeds" in result.lower()


def test_malformed_json_body() -> None:
    """Valid Content-Type but malformed JSON body returns parse error."""
    resp = make_response(b"not json at all", "application/json")
    result = process_response(resp)
    assert isinstance(result, str)
    assert "parse error" in result.lower()


def test_empty_body() -> None:
    """Empty body returns parse error (empty is not valid JSON object)."""
    resp = make_response(b"", "application/json")
    result = process_response(resp)
    assert isinstance(result, str)


def test_content_length_just_under_limit() -> None:
    """Content-Length just under 10MB succeeds."""
    size = str(MAX_RESPONSE_SIZE)
    body = b'{"k": "v"}'
    resp = make_response(body, "application/json", size)
    result = process_response(resp)
    assert isinstance(result, dict)


def test_pre_read_body_skips_streaming() -> None:
    """Pipeline with pre_read_body skips Content-Length and streaming."""
    resp = make_response(content_type="application/json")
    body = b'{"pre": "read"}'
    result = process_response(resp, pre_read_body=body)
    assert isinstance(result, dict)
    assert result["pre"] == "read"


def test_pre_read_body_rejects_non_json_content_type() -> None:
    """Pipeline with pre_read_body and non-JSON Content-Type still rejects."""
    resp = make_response(content_type="text/plain")
    body = b'{"pre": "read"}'
    result = process_response(resp, pre_read_body=body)
    assert isinstance(result, str)
    assert "Content-Type" in result
