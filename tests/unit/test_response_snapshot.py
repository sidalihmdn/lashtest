"""Unit tests for Response.assert_snapshot."""

import pytest
from unittest.mock import MagicMock
from datetime import timedelta
from lashtest.core.response import Response
from lashtest.assertions.snapshot import SnapshotMismatchError


def make_response(json_data):
    raw = MagicMock()
    raw.status_code = 200
    raw.headers = {"Content-Type": "application/json"}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.text = ""
    raw.json.return_value = json_data
    return Response(raw)


class TestResponseAssertSnapshot:

    def test_creates_snapshot_on_first_call(self, tmp_path):
        r = make_response({"id": 1, "name": "Alice"})
        r.assert_snapshot("user", snapshot_dir=str(tmp_path))
        assert (tmp_path / "user.json").exists()

    def test_passes_on_matching_response(self, tmp_path):
        payload = {"id": 1, "name": "Alice"}
        r1 = make_response(payload)
        r1.assert_snapshot("user", snapshot_dir=str(tmp_path))
        r2 = make_response(payload)
        r2.assert_snapshot("user", snapshot_dir=str(tmp_path))

    def test_fails_on_mismatched_response(self, tmp_path):
        r1 = make_response({"id": 1, "name": "Alice"})
        r1.assert_snapshot("user", snapshot_dir=str(tmp_path))
        r2 = make_response({"id": 1, "name": "Bob"})
        with pytest.raises(SnapshotMismatchError):
            r2.assert_snapshot("user", snapshot_dir=str(tmp_path))

    def test_ignore_skips_dynamic_fields(self, tmp_path):
        r1 = make_response({"id": 1, "created_at": "2024-01-01"})
        r1.assert_snapshot("ts", ignore=["created_at"], snapshot_dir=str(tmp_path))
        r2 = make_response({"id": 1, "created_at": "2025-06-15"})
        r2.assert_snapshot("ts", ignore=["created_at"], snapshot_dir=str(tmp_path))

    def test_update_overwrites_snapshot(self, tmp_path):
        r1 = make_response({"v": 1})
        r1.assert_snapshot("snap", snapshot_dir=str(tmp_path))
        r2 = make_response({"v": 2})
        r2.assert_snapshot("snap", update=True, snapshot_dir=str(tmp_path))
        r3 = make_response({"v": 2})
        r3.assert_snapshot("snap", snapshot_dir=str(tmp_path))  # should pass

    def test_returns_self_for_chaining(self, tmp_path):
        r = make_response({"id": 1})
        result = r.assert_snapshot("x", snapshot_dir=str(tmp_path))
        assert result is r
