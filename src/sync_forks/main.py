#!/usr/bin/env python3
"""CLI entry point for sync-forks."""
from __future__ import annotations

import click


@click.command()
@click.argument("filename")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes.")
@click.option("--quiet", is_flag=True, help="Suppress non-error output.")
def cli(filename: str, dry_run: bool, quiet: bool) -> None:
    """Sync GitHub forks from a list in FILENAME (or - for stdin)."""
