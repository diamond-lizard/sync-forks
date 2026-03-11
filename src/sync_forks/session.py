#!/usr/bin/env python3
"""Session factory for configured requests.Session instances."""
from __future__ import annotations

import requests

from sync_forks.auth import GitHubAuth
from sync_forks.constants import REQUIRED_HEADERS


def create_session(token: str) -> requests.Session:
    """Create a requests.Session with GitHub headers and auth.

    Configures the session with required Accept, API version, and
    User-Agent headers, and attaches GitHubAuth for host-restricted
    Bearer token authentication.
    """
    session = requests.Session()
    session.headers.update(REQUIRED_HEADERS)
    session.auth = GitHubAuth(token)
    return session
