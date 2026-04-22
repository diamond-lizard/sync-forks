#!/usr/bin/env python3
"""Error diagnosis and actionable hint generation for sync-forks."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.sync_error import SyncError

from sync_forks.diagnostics_rules import (
    check_5xx,
    check_403,
    check_404,
    check_409,
    check_422_workflow,
    check_all_401,
    check_network,
)


def diagnose_errors(errors: list[SyncError]) -> list[str]:
    """Analyze collected errors and return actionable hint strings.

    Returns an empty list when no useful hints can be generated.
    Each hint is prefixed with 'Hint: '.
    """
    if not errors:
        return []
    hints: list[str] = []
    check_all_401(errors, hints)
    check_422_workflow(errors, hints)
    check_404(errors, hints)
    check_409(errors, hints)
    check_403(errors, hints)
    check_network(errors, hints)
    check_5xx(errors, hints)
    return hints


def print_diagnostics(errors: list[SyncError]) -> None:
    """Print diagnostic hints to stderr if any are applicable.

    Always prints regardless of quiet mode, since diagnostics
    are actionable error guidance.
    """
    for hint in diagnose_errors(errors):
        print(hint, file=sys.stderr)
