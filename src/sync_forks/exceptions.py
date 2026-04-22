#!/usr/bin/env python3
"""Exception types for sync-forks abort handling."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.types import SyncResult


class SyncAbortError(Exception):
    """Wraps abort exceptions to carry partial SyncResult."""

    partial_result: SyncResult

    def __init__(self, partial_result: SyncResult, cause: BaseException) -> None:
        """Store partial result and chain the original cause."""
        super().__init__(str(cause))
        self.partial_result = partial_result
        self.__cause__ = cause
