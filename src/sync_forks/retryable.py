#!/usr/bin/env python3
"""5xx single-retry logic for GitHub API requests."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import requests

from sync_forks.constants import FIVE_XX_RETRY_DELAY
from sync_forks.errors import is_server_error


def retry_on_5xx(
    response: requests.Response,
    retry_request: Callable[[], requests.Response],
) -> requests.Response:
    """Retry once on 5xx, returning the final response.

    If the original response is not 5xx, returns it unchanged.
    On 5xx, waits FIVE_XX_RETRY_DELAY seconds and calls retry_request()
    to re-execute the request.

    If the retry succeeds (non-5xx), returns the successful response.
    If the retry is also 5xx, returns the retry response (caller
    should count 1 error toward per-host threshold).
    If the retry is rate-limited (403/429), returns it so the caller's
    rate limit detection handles it.
    """
    if not is_server_error(response.status_code):
        return response
    time.sleep(FIVE_XX_RETRY_DELAY)
    return retry_request()
