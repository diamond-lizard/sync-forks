#!/usr/bin/env python3
"""Tests for SyncError types and constructor helpers."""
from __future__ import annotations

import pytest
from sync_forks.sync_error import (
    ApiResult,
    BranchResult,
    MergeResult,
    SyncError,
    http_error,
    missing_field_error,
    network_error,
    parse_error,
)


def test_sync_error_is_frozen() -> None:
    """SyncError instances are immutable."""
    err = SyncError(repo="o/r", kind="http", operation="merge_upstream")
    with pytest.raises(AttributeError):
        err.repo = "other"  # type: ignore[misc]


def test_http_error_constructor() -> None:
    """http_error sets kind='http' and stores status_code and api_message."""
    err = http_error("o/r", "merge_upstream", 422, "workflow scope")
    assert err.kind == "http"
    assert err.status_code == 422
    assert err.api_message == "workflow scope"
    assert err.operation == "merge_upstream"


def test_network_error_constructor() -> None:
    """network_error sets kind='network' and stores exception detail."""
    exc = ConnectionError("refused")
    err = network_error("o/r", "get_default_branch", exc)
    assert err.kind == "network"
    assert "refused" in (err.detail or "")
    assert err.status_code is None


def test_parse_error_constructor() -> None:
    """parse_error sets kind='parse' and stores detail string."""
    err = parse_error("o/r", "get_default_branch", "JSON parse error")
    assert err.kind == "parse"
    assert err.detail == "JSON parse error"


def test_missing_field_error_constructor() -> None:
    """missing_field_error sets kind='missing_field' with field in detail."""
    err = missing_field_error("o/r", "get_default_branch", "default_branch")
    assert err.kind == "missing_field"
    assert "default_branch" in (err.detail or "")


def test_api_result_success() -> None:
    """ApiResult with data and no error represents success."""
    r = ApiResult(data={"key": "val"}, error=None)
    assert r.data is not None
    assert r.error is None


def test_api_result_failure() -> None:
    """ApiResult with no data and an error represents failure."""
    err = http_error("o/r", "merge_upstream", 500, None)
    r = ApiResult(data=None, error=err)
    assert r.data is None
    assert r.error is err


def test_branch_result_fields() -> None:
    """BranchResult stores branch and error."""
    r = BranchResult(branch="main", error=None)
    assert r.branch == "main"
    assert r.error is None


def test_merge_result_fields() -> None:
    """MergeResult stores ok flag and error."""
    r = MergeResult(ok=False, error=http_error("o/r", "merge_upstream", 422, None))
    assert r.ok is False
    assert r.error is not None
