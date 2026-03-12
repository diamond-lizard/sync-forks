#!/usr/bin/env python3
"""Additional tests for sync_forks.output module."""
from __future__ import annotations

import io
import sys

from helpers import make_fork_entry, make_sync_result

from sync_forks.output import (
    make_rate_limit_notifier,
    print_ahead_and_behind_report,
    print_dry_run_would_sync,
    print_summary,
)


def test_quiet_suppresses_summary() -> None:
    """Quiet mode suppresses summary output."""
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_summary(make_sync_result(synced=["a"]), [], quiet=True)
    finally:
        sys.stderr = sys.__stderr__
    assert buf.getvalue() == ""


def test_rate_limit_notification_format() -> None:
    """Rate limit notification matches expected pattern."""
    buf = io.StringIO()
    sys.stderr = buf
    try:
        notifier = make_rate_limit_notifier(quiet=False)
        notifier(58)
    finally:
        sys.stderr = sys.__stderr__
    assert "Rate limited. Waiting 58s before retrying..." in buf.getvalue()


def test_rate_limit_notification_quiet() -> None:
    """Rate limit notification suppressed in quiet mode."""
    buf = io.StringIO()
    sys.stderr = buf
    try:
        notifier = make_rate_limit_notifier(quiet=True)
        notifier(58)
    finally:
        sys.stderr = sys.__stderr__
    assert buf.getvalue() == ""


def test_ahead_and_behind_report_lists_all() -> None:
    """Ahead-and-behind report lists all skipped repos."""
    entries = [
        make_fork_entry("https://github.com/alice/foo", 1, 2),
        make_fork_entry("https://github.com/bob/bar", 3, 4),
    ]
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_ahead_and_behind_report(entries, quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    out = buf.getvalue()
    assert "Skipped alice/foo (ahead and behind)." in out
    assert "Skipped bob/bar (ahead and behind)." in out


def test_ahead_and_behind_report_quiet() -> None:
    """Ahead-and-behind report suppressed in quiet mode."""
    entries = [make_fork_entry("https://github.com/alice/foo", 1, 2)]
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_ahead_and_behind_report(entries, quiet=True)
    finally:
        sys.stderr = sys.__stderr__
    assert buf.getvalue() == ""


def test_dry_run_would_sync_output() -> None:
    """Dry-run output shows which repos would be synced."""
    buf = io.StringIO()
    sys.stderr = buf
    try:
        print_dry_run_would_sync("alice", "foo", quiet=False)
    finally:
        sys.stderr = sys.__stderr__
    assert "Would sync alice/foo." in buf.getvalue()
