#!/usr/bin/env python3
"""Tests for the diagnostics module."""
from __future__ import annotations

from sync_forks.diagnostics import diagnose_errors

from sync_forks.sync_error import SyncError, network_error


def _make(kind: str = "http", status: int | None = None, msg: str | None = None) -> SyncError:
    """Shorthand to build a SyncError for testing."""
    return SyncError(
        repo="o/r", kind=kind, operation="merge_upstream",
        status_code=status, api_message=msg,
    )


def test_empty_errors_no_hints() -> None:
    """No errors produces no hints."""
    assert diagnose_errors([]) == []


def test_all_401_auth_hint() -> None:
    """All errors being 401 produces an authentication hint."""
    errors = [_make(status=401), _make(status=401)]
    hints = diagnose_errors(errors)
    assert any("authentication" in h.lower() for h in hints)


def test_422_workflow_hint() -> None:
    """A 422 with 'workflow' in the message produces a Workflows hint."""
    errors = [_make(status=422, msg="refusing to allow without workflow scope")]
    hints = diagnose_errors(errors)
    assert any("workflows" in h.lower() for h in hints)


def test_422_workflow_case_insensitive() -> None:
    """The workflow keyword match is case-insensitive."""
    errors = [_make(status=422, msg="WORKFLOW scope required")]
    hints = diagnose_errors(errors)
    assert any("workflows" in h.lower() for h in hints)


def test_404_access_hint() -> None:
    """A 404 error produces an access/private hint."""
    errors = [_make(status=404)]
    hints = diagnose_errors(errors)
    assert any("404" in h for h in hints)


def test_409_diverged_hint() -> None:
    """A 409 error produces a diverged/rebase hint."""
    errors = [_make(status=409)]
    hints = diagnose_errors(errors)
    assert any("diverged" in h.lower() for h in hints)


def test_403_permission_hint() -> None:
    """A 403 error produces a permission hint."""
    errors = [_make(status=403)]
    hints = diagnose_errors(errors)
    assert any("403" in h for h in hints)


def test_network_error_hint() -> None:
    """Network errors produce a connection hint."""
    errors = [network_error("o/r", "get_default_branch", ConnectionError("refused"))]
    hints = diagnose_errors(errors)
    assert any("network" in h.lower() for h in hints)


def test_5xx_transient_hint() -> None:
    """Multiple 5xx errors produce a transient/retry hint."""
    errors = [_make(status=500), _make(status=502)]
    hints = diagnose_errors(errors)
    assert any("server error" in h.lower() for h in hints)


def test_mixed_errors_multiple_hints() -> None:
    """Mixed error types produce multiple relevant hints."""
    errors = [
        _make(status=422, msg="workflow scope"),
        _make(status=409),
    ]
    hints = diagnose_errors(errors)
    assert len(hints) >= 2


def test_401_mixed_with_others_no_all_auth_hint() -> None:
    """401 mixed with other codes does NOT produce 'all auth' hint."""
    errors = [_make(status=401), _make(status=422)]
    hints = diagnose_errors(errors)
    all_auth = [h for h in hints if "all failures are authentication" in h.lower()]
    assert len(all_auth) == 0


def test_hints_are_prefixed() -> None:
    """All hints start with 'Hint: '."""
    errors = [_make(status=404)]
    hints = diagnose_errors(errors)
    assert all(h.startswith("Hint: ") for h in hints)
