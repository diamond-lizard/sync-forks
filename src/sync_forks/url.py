#!/usr/bin/env python3
"""URL parsing and owner/repo extraction with GitHub naming validation."""
from __future__ import annotations

import re
import sys
from urllib.parse import urlparse

_GITHUB_NAME_RE: re.Pattern[str] = re.compile(r"^[A-Za-z0-9\-._]+$")


def parse_owner_repo(repo_url: str) -> tuple[str, str] | None:
    """Parse a repo URL into (owner, repo), or None if invalid.

    Validates that the URL path has exactly two components and each
    component matches GitHub's naming conventions.  Reports errors
    on stderr.
    """
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        print(f"Warning: invalid repo URL path '{repo_url}': expected owner/repo.", file=sys.stderr)
        return None
    owner, repo = parts[0], parts[1]
    if not _validate_name(owner, "owner", repo_url):
        return None
    if not _validate_name(repo, "repo", repo_url):
        return None
    return owner, repo


def _validate_name(name: str, label: str, repo_url: str) -> bool:
    """Validate a single name component against GitHub naming conventions.

    Returns True if valid, prints warning to stderr and returns False otherwise.
    """
    if not _GITHUB_NAME_RE.match(name):
        print(f"Warning: invalid {label} '{name}' in URL '{repo_url}'.", file=sys.stderr)
        return False
    return True
