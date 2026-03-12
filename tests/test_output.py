#!/usr/bin/env python3
"""Tests for sync_forks.output module."""
from __future__ import annotations

from helpers import make_fork_entry, make_sync_result

from sync_forks.output import (
    print_dry_run_would_sync,
    print_skipped,
    print_summary,
    print_sync_failed,
    print_synced,
    print_syncing,
)


def test_summary_all_synced(capsys: object) -> None:
    """Summary shows synced count when all succeed."""
    import io
    import sys
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_summary(make_sync_result(synced=["a", "b", "c"]), [], quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    assert "Synced 3 repos" in buf.getvalue()


def test_summary_with_errors() -> None:
    """Summary shows error count."""
    import io
    import sys
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_summary(make_sync_result(synced=["a"], failed=["b", "c"]), [], quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    out = buf.getvalue()
    assert "Synced 1 repos" in out
    assert "2 errors" in out


def test_summary_with_skipped() -> None:
    """Summary shows skipped count for ahead-and-behind."""
    import io
    import sys
    buf = io.StringIO()
    sys.stderr = buf
    try:
        aab = [make_fork_entry("https://github.com/o/r", 1, 2)]
        print_summary(make_sync_result(synced=["a"]), aab, quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    assert "skipped 1 (ahead-and-behind)" in buf.getvalue()


def test_summary_nothing_to_do() -> None:
    """Summary shows 'Nothing to do' when all lists are empty."""
    import io
    import sys
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_summary(make_sync_result(), [], quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    assert "Nothing to do" in buf.getvalue()


def test_quiet_suppresses_per_repo() -> None:
    """Quiet mode suppresses per-repo messages."""
    import io
    import sys
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_syncing("o", "r", quiet=True)
        print_synced("o", "r", quiet=True)
        print_sync_failed("o", "r", "err", quiet=True)
        print_skipped("o", "r", quiet=True)
        print_dry_run_would_sync("o", "r", quiet=True)
    finally:
        sys.stderr = sys.__stderr__
    assert buf.getvalue() == ""
