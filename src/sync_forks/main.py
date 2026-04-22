#!/usr/bin/env python3
"""CLI entry point for sync-forks."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from sync_forks.types import ForkEntry


@click.command()
@click.argument("filename")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes.")
@click.option("--quiet", is_flag=True, help="Suppress non-error output.")
def cli(filename: str, dry_run: bool, quiet: bool) -> None:
    """Sync GitHub forks from a list in FILENAME (or - for stdin)."""
    from sync_forks.main_helpers import parse_and_classify, report_ahead_and_behind, report_dry_run

    classified = parse_and_classify(filename)
    behind = classified["behind_only"]
    ahead_behind = classified["ahead_and_behind"]
    if not behind and not ahead_behind:
        _msg("All forks are up to date.", quiet=quiet)
        return
    report_ahead_and_behind(ahead_behind, quiet=quiet)
    if dry_run:
        report_dry_run(behind, quiet=quiet)
        return
    if not behind:
        _msg("No behind-only forks to sync.", quiet=quiet)
        return
    _execute_sync(behind, ahead_behind, quiet=quiet)


def _msg(text: str, *, quiet: bool) -> None:
    """Print an informational message to stderr unless quiet."""
    if not quiet:
        print(text, file=sys.stderr)


def _print_abort_reason(cause: BaseException | None) -> None:
    """Print abort reason to stderr, using 'Interrupted.' for KeyboardInterrupt."""
    msg = "Interrupted." if isinstance(cause, KeyboardInterrupt) else f"Aborted: {cause}"
    print(msg, file=sys.stderr)


def _execute_sync(
    behind: list[ForkEntry],
    ahead_behind: list[ForkEntry],
    *,
    quiet: bool,
) -> None:
    """Retrieve token, create session, run sync, handle aborts."""
    from sync_forks.diagnostics import print_diagnostics
    from sync_forks.exceptions import SyncAbortError
    from sync_forks.output import make_rate_limit_notifier, print_summary
    from sync_forks.session import create_session
    from sync_forks.sync import sync_repos
    from sync_forks.token import retrieve_token

    token = retrieve_token()
    session = create_session(token)
    notifier = make_rate_limit_notifier(quiet=quiet)
    try:
        result = sync_repos(behind, session, quiet=quiet, on_rate_limit=notifier)
    except SyncAbortError as exc:
        print_summary(exc.partial_result, ahead_behind, quiet=quiet)
        print_diagnostics(exc.partial_result["errors"])
        _print_abort_reason(exc.__cause__)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(1)
    print_summary(result, ahead_behind, quiet=quiet)
    print_diagnostics(result["errors"])
