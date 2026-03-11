#!/usr/bin/env python3
"""GitHub token retrieval from the pass password manager."""
from __future__ import annotations

import subprocess
import sys

from sync_forks.constants import PASS_COMMAND, PASS_TIMEOUT


def retrieve_token() -> str:
    """Invoke pass to retrieve the GitHub token.

    Returns the first line of pass output, stripped of trailing whitespace.
    Prints a descriptive error to stderr and exits with code 1 on failure.
    """
    try:
        result = subprocess.run(
            PASS_COMMAND,
            capture_output=True,
            text=True,
            timeout=PASS_TIMEOUT,
        )
    except FileNotFoundError:
        print("Error: 'pass' not found on PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        _exit_with_error(f"Error: 'pass' timed out after {PASS_TIMEOUT}s.")
    if result.returncode != 0:
        stderr_msg = result.stderr.strip()
        _exit_with_error(
            f"Error: 'pass' exited with code {result.returncode}: {stderr_msg}",
        )
    token = _extract_first_line(result.stdout)
    if not token:
        _exit_with_error("Error: 'pass' returned empty output.")
    return token


def _extract_first_line(output: str) -> str:
    """Return the first line of output, stripped of trailing whitespace."""
    first_line = output.split("\n", maxsplit=1)[0]
    return first_line.rstrip()


def _exit_with_error(message: str) -> None:
    """Print an error message to stderr and exit with code 1."""
    print(message, file=sys.stderr)
    sys.exit(1)
