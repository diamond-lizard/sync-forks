#!/usr/bin/env python3
"""AuthBase subclass restricting Authorization header to api.github.com."""
from __future__ import annotations

from urllib.parse import urlparse

import requests.auth

from sync_forks.constants import API_HOST


class GitHubAuth(requests.auth.AuthBase):
    """Add Bearer token only when the request targets api.github.com."""

    def __init__(self, token: str) -> None:
        """Store the token for later use."""
        self._token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        """Attach Authorization header if the request host is api.github.com."""
        if r.url and urlparse(r.url).hostname == API_HOST:
            r.headers["Authorization"] = f"Bearer {self._token}"
        return r
