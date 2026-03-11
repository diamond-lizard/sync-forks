#!/usr/bin/env python3
"""Shared test helper functions."""
from __future__ import annotations

import io

import requests


def make_response(
    body: bytes = b"{}",
    content_type: str = "application/json",
    content_length: str | None = None,
) -> requests.Response:
    """Build a constructed requests.Response for testing."""
    resp = requests.Response()
    resp.status_code = 200
    resp.headers["Content-Type"] = content_type
    if content_length is not None:
        resp.headers["Content-Length"] = content_length
    resp.raw = io.BytesIO(body)
    resp.encoding = "utf-8"
    return resp
