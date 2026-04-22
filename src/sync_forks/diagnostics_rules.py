#!/usr/bin/env python3
"""Individual diagnostic rule functions for error analysis."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.sync_error import SyncError


def check_all_401(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when every error is a 401 authentication failure."""
    if all(e.status_code == 401 for e in errors):
        hints.append(
            "Hint: All failures are authentication errors."
            " Your token may be expired or invalid.",
        )


def check_422_workflow(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when any 422 mentions workflow scope."""
    for e in errors:
        if e.status_code == 422 and e.api_message and "workflow" in e.api_message.lower():
            hints.append(
                "Hint: Some failures need the Workflows"
                " permission on your token.",
            )
            return


def check_404(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when any error is a 404."""
    if any(e.status_code == 404 for e in errors):
        hints.append(
            "Hint: Some repos returned 404."
            " They may be private or your token may lack access.",
        )


def check_409(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when any error is a 409 Conflict."""
    if any(e.status_code == 409 for e in errors):
        hints.append(
            "Hint: Some repos have diverged from upstream."
            " Merge or rebase them manually.",
        )


def check_403(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when any error is a 403 Forbidden."""
    if any(e.status_code == 403 for e in errors):
        hints.append(
            "Hint: Some repos returned 403 Forbidden."
            " Your token may lack required permissions.",
        )


def check_network(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when any error is a network failure."""
    if any(e.kind == "network" for e in errors):
        hints.append(
            "Hint: Some failures are network errors."
            " Check your connection and try again.",
        )


def check_5xx(errors: list[SyncError], hints: list[str]) -> None:
    """Hint when multiple 5xx server errors occurred."""
    count = sum(1 for e in errors if e.status_code and 500 <= e.status_code < 600)
    if count >= 2:
        hints.append(
            "Hint: GitHub returned server errors."
            " This is usually transient — try again later.",
        )
