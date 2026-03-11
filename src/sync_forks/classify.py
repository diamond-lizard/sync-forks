#!/usr/bin/env python3
"""Fork classification by sync status."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.types import ClassifiedForks, ForkEntry


def classify_forks(forks: list[ForkEntry]) -> ClassifiedForks:
    """Classify forks into behind-only and ahead-and-behind categories.

    Entries with behind_by == 0 are excluded (already up to date or ahead only).
    behind-only: behind_by > 0 and ahead_by == 0.
    ahead-and-behind: behind_by > 0 and ahead_by > 0.
    """
    behind_only: list[ForkEntry] = []
    ahead_and_behind: list[ForkEntry] = []
    for fork in forks:
        if fork["behind_by"] <= 0:
            continue
        if fork["ahead_by"] == 0:
            behind_only.append(fork)
        else:
            ahead_and_behind.append(fork)
    return {"behind_only": behind_only, "ahead_and_behind": ahead_and_behind}
