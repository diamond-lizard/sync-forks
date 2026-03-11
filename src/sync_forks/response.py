#!/usr/bin/env python3
"""Response processing pipeline for GitHub API responses."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests

from sync_forks.constants import MAX_RESPONSE_SIZE


def check_content_length(response: requests.Response) -> str | None:
    """Return error string if Content-Length exceeds max, else None."""
    length_str = response.headers.get("Content-Length")
    if length_str is None:
        return None
    try:
        length = int(length_str)
    except ValueError:
        return None
    if length > MAX_RESPONSE_SIZE:
        return f"Response too large: {length} bytes"
    return None


def check_content_type(response: requests.Response) -> str | None:
    """Return error string if Content-Type does not contain 'json', else None."""
    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type:
        return f"Unexpected Content-Type: {content_type}"
    return None


def read_body_streaming(response: requests.Response) -> bytes | str:
    """Read response body via iter_content with size limit.

    Returns accumulated bytes on success, error string if size exceeded.
    """
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=8192):
        total += len(chunk)
        if total > MAX_RESPONSE_SIZE:
            return f"Response body exceeds {MAX_RESPONSE_SIZE} bytes"
        chunks.append(chunk)
    return b"".join(chunks)


def parse_json(data: bytes) -> dict[str, object] | str:
    """Parse bytes as JSON, validating the result is a dict.

    Returns parsed dict on success, error string on failure.
    """
    try:
        parsed: object = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        return f"JSON parse error: {exc}"
    if not isinstance(parsed, dict):
        return f"Expected JSON object, got {type(parsed).__name__}"
    return parsed


def process_response(
    response: requests.Response,
    pre_read_body: bytes | None = None,
) -> dict[str, object] | str:
    """Run the full response processing pipeline.

    When pre_read_body is provided, skips Content-Length check and
    streaming read, proceeding directly to Content-Type and JSON parse.
    Returns parsed dict on success, error string on failure.
    """
    if pre_read_body is None:
        error = check_content_length(response)
        if error:
            return error
    error = check_content_type(response)
    if error:
        return error
    if pre_read_body is not None:
        return parse_json(pre_read_body)
    body_result = read_body_streaming(response)
    if isinstance(body_result, str):
        return body_result
    return parse_json(body_result)
