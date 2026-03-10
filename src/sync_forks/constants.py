#!/usr/bin/env python3
"""Shared constants for the sync-forks tool."""
from __future__ import annotations

REQUEST_TIMEOUT: int = 30
MUTATIVE_REQUEST_DELAY: float = 1.0
NON_MUTATIVE_REQUEST_DELAY: float = 0.1
MAX_RESPONSE_SIZE: int = 10 * 1024 * 1024
PER_HOST_ERROR_THRESHOLD: int = 5
MAX_RATE_LIMIT_RETRIES: int = 10
FIVE_XX_RETRY_DELAY: float = 5.0
PASS_TIMEOUT: int = 30
PASS_COMMAND: tuple[str, ...] = ("pass", "show", "github.com/fgpat/repos-rw")

REQUIRED_HEADERS: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "sync-forks",
}

API_HOST: str = "api.github.com"
