#!/usr/bin/env python3
"""Shared request execution with retry, rate limit, and error tracking."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from collections.abc import Callable

    from sync_forks.retry import RateLimitRetrier

import requests

from sync_forks.constants import API_HOST
from sync_forks.errors import (
    classify_http_error,
    classify_network_error,
    is_server_error,
    is_threshold_countable,
    record_error,
    report_error,
)
from sync_forks.ratelimit import detect_rate_limit
from sync_forks.response import process_response
from sync_forks.retryable import retry_on_5xx
from sync_forks.sync_error import (
    ApiResult,
    extract_api_message,
    http_error,
    network_error,
    parse_error,
)


def build_repo_url(owner: str, repo: str) -> str:
    """Build the API URL for a repo, URL-encoding path parameters."""
    return f"https://{API_HOST}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"


def execute_api_call(
    make_request: Callable[[], requests.Response],
    delay: float,
    retrier: RateLimitRetrier,
    error_tracker: dict[str, int],
    owner: str,
    repo: str,
    operation: str,
) -> ApiResult:
    """Execute an API call with retry, rate limit, and error tracking.

    Returns ApiResult with parsed data on success, or structured error on failure.
    """
    repo_id = f"{owner}/{repo}"
    pre_read_body: bytes | None = None
    while True:
        try:
            response = make_request()
        except requests.RequestException as exc:
            report_error(classify_network_error(exc, owner, repo))
            record_error(error_tracker, API_HOST)
            return ApiResult(None, network_error(repo_id, operation, exc))
        time.sleep(delay)
        try:
            response = retry_on_5xx(response, make_request)
        except requests.RequestException as exc:
            report_error(classify_network_error(exc, owner, repo))
            record_error(error_tracker, API_HOST)
            return ApiResult(None, network_error(repo_id, operation, exc))
        if response.status_code not in (403, 429):
            break
        verdict = detect_rate_limit(response)
        if not verdict.is_rate_limit:
            pre_read_body = verdict.pre_read_body
            break
        time.sleep(retrier.handle(response))
    retrier.reset()
    if is_server_error(response.status_code):
        msg = extract_api_message(response, pre_read_body)
        report_error(classify_http_error(response.status_code, owner, repo, api_message=msg))
        record_error(error_tracker, API_HOST)
        return ApiResult(None, http_error(repo_id, operation, response.status_code, msg))
    if not response.ok:
        msg = extract_api_message(response, pre_read_body)
        report_error(classify_http_error(response.status_code, owner, repo, api_message=msg))
        if is_threshold_countable(response.status_code):
            record_error(error_tracker, API_HOST)
        return ApiResult(None, http_error(repo_id, operation, response.status_code, msg))
    result = process_response(response, pre_read_body)
    if isinstance(result, str):
        report_error(f"{owner}/{repo}: {result}")
        return ApiResult(None, parse_error(repo_id, operation, result))
    return ApiResult(result, None)
