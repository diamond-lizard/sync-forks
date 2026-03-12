#!/usr/bin/env python3
"""Tests for keyboard interrupt and abort signal handling."""
from __future__ import annotations

import io
import sys

from helpers import make_sync_result

from sync_forks.main import _print_abort_reason
from sync_forks.sync import SyncAbortError


def _capture_abort_reason(cause: BaseException | None) -> str:
    """Capture stderr output from _print_abort_reason."""
    buf = io.StringIO()
    old = sys.stderr
    sys.stderr = buf
    try:
        _print_abort_reason(cause)
    finally:
        sys.stderr = old
    return buf.getvalue()


def test_keyboard_interrupt_prints_interrupted() -> None:
    """KeyboardInterrupt cause prints 'Interrupted.' to stderr."""
    out = _capture_abort_reason(KeyboardInterrupt())
    assert "Interrupted." in out


def test_keyboard_interrupt_no_traceback() -> None:
    """KeyboardInterrupt cause does not include traceback text."""
    out = _capture_abort_reason(KeyboardInterrupt())
    assert "Traceback" not in out


def test_other_abort_prints_aborted() -> None:
    """Non-interrupt cause prints 'Aborted: ...' to stderr."""
    cause = RuntimeError("host threshold exceeded")
    out = _capture_abort_reason(cause)
    assert "Aborted:" in out
    assert "host threshold exceeded" in out


def test_abort_via_sync_abort_error() -> None:
    """SyncAbortError with KeyboardInterrupt cause exits 1."""
    exc = SyncAbortError(make_sync_result(synced=["o/a"]), KeyboardInterrupt())
    assert isinstance(exc.__cause__, KeyboardInterrupt)
    out = _capture_abort_reason(exc.__cause__)
    assert "Interrupted." in out
    assert "Aborted" not in out


def test_quiet_suppresses_summary_not_interrupted() -> None:
    """Quiet mode suppresses summary but 'Interrupted.' still prints."""
    from sync_forks.output import print_summary
    buf = io.StringIO()
    old = sys.stderr
    sys.stderr = buf
    try:
        print_summary(make_sync_result(synced=["a"]), [], quiet=True)
        _print_abort_reason(KeyboardInterrupt())
    finally:
        sys.stderr = old
    out = buf.getvalue()
    assert "Synced" not in out
    assert "Interrupted." in out
