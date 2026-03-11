#!/usr/bin/env python3
"""Input reading, JSON parsing, and fork entry validation."""
from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sync_forks.types import ForkEntry


def read_input(filename: str) -> str:
    """Read raw input from a file path or stdin when filename is '-'."""
    if filename == "-":
        return sys.stdin.read()
    try:
        with open(filename) as f:
            return f.read()
    except OSError as exc:
        print(f"Error reading '{filename}': {exc}", file=sys.stderr)
        sys.exit(1)


def parse_json(raw: str) -> object:
    """Parse a JSON string, exit with code 1 on parse error."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def validate_structure(data: object) -> list[object]:
    """Validate top-level structure: dict with 'results' list. Exit 1 if invalid."""
    if not isinstance(data, dict):
        print("Error: JSON root must be an object.", file=sys.stderr)
        sys.exit(1)
    results = data.get("results")
    if not isinstance(results, list):
        print("Error: JSON root must contain a 'results' array.", file=sys.stderr)
        sys.exit(1)
    return results


def _validate_fork_entry(entry: dict[str, object], index: int) -> ForkEntry | None:
    """Validate a single fork entry. Return ForkEntry or None with stderr warning."""
    for field in ("repo_url", "ahead_by", "behind_by"):
        if field not in entry:
            print(f"Warning: entry {index}: missing '{field}', skipping.", file=sys.stderr)
            return None
    url = entry["repo_url"]
    ahead = entry["ahead_by"]
    behind = entry["behind_by"]
    if not isinstance(url, str):
        print(f"Warning: entry {index}: 'repo_url' not a string, skipping.", file=sys.stderr)
        return None
    if not isinstance(ahead, int) or isinstance(ahead, bool):
        print(f"Warning: entry {index}: 'ahead_by' not an integer, skipping.", file=sys.stderr)
        return None
    if not isinstance(behind, int) or isinstance(behind, bool):
        print(f"Warning: entry {index}: 'behind_by' not an integer, skipping.", file=sys.stderr)
        return None
    return {"repo_url": url, "ahead_by": ahead, "behind_by": behind}


def extract_fork_entries(results: list[object]) -> list[ForkEntry]:
    """Extract and validate fork entries from results. Skip non-forks and invalid entries."""
    forks: list[ForkEntry] = []
    for i, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "fork":
            continue
        validated = _validate_fork_entry(item, i)
        if validated is not None:
            forks.append(validated)
    return forks
