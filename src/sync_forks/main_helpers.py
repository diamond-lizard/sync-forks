#!/usr/bin/env python3
"""Helper functions for CLI entry point."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.types import ClassifiedForks, ForkEntry


def parse_and_classify(filename: str) -> ClassifiedForks:
    """Read, parse, validate input and classify forks."""
    from sync_forks.classify import classify_forks
    from sync_forks.input import extract_fork_entries, parse_json, read_input, validate_structure

    raw = read_input(filename)
    data = parse_json(raw)
    results = validate_structure(data)
    forks = extract_fork_entries(results)
    return classify_forks(forks)


def report_ahead_and_behind(
    entries: list[ForkEntry], *, quiet: bool,
) -> None:
    """Report ahead-and-behind repos on stderr."""
    from sync_forks.output import print_ahead_and_behind_report

    print_ahead_and_behind_report(entries, quiet=quiet)


def report_dry_run(behind: list[ForkEntry], *, quiet: bool) -> None:
    """Print dry-run report showing which repos would be synced."""
    from sync_forks.output import print_dry_run_would_sync
    from sync_forks.url import parse_owner_repo

    for entry in behind:
        parsed = parse_owner_repo(entry["repo_url"])
        if parsed:
            print_dry_run_would_sync(parsed[0], parsed[1], quiet=quiet)
