"""Unit tests for response snapshot assertions."""

import json
import pytest
from pathlib import Path
from lashtest.assertions.snapshot import SnapshotStore, SnapshotMismatchError


def make_store(tmp_path, update=False):
    return SnapshotStore(snapshot_dir=tmp_path / "snapshots", update=update)


class TestSnapshotStoreJson:

    def test_creates_snapshot_on_first_call(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("user", {"id": 1, "name": "Alice"})
        snap_file = tmp_path / "snapshots" / "user.json"
        assert snap_file.exists()

    def test_stored_content_is_valid_json(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("item", {"price": 9.99})
        data = json.loads((tmp_path / "snapshots" / "item.json").read_text())
        assert data == {"price": 9.99}

    def test_passes_when_value_matches_stored_snapshot(self, tmp_path):
        store = make_store(tmp_path)
        payload = {"id": 1, "name": "Alice"}
        store.assert_json("user", payload)  # creates
        store.assert_json("user", payload)  # compares — must pass

    def test_raises_on_mismatch(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("user", {"id": 1, "name": "Alice"})  # create
        with pytest.raises(SnapshotMismatchError):
            store.assert_json("user", {"id": 1, "name": "Bob"})  # mismatch

    def test_mismatch_error_contains_snapshot_name(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("my_snap", {"x": 1})
        with pytest.raises(SnapshotMismatchError) as exc_info:
            store.assert_json("my_snap", {"x": 2})
        assert "my_snap" in str(exc_info.value)

    def test_update_flag_overwrites_snapshot(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("user", {"id": 1, "name": "Alice"})  # create
        update_store = make_store(tmp_path, update=True)
        update_store.assert_json("user", {"id": 1, "name": "Bob"})  # overwrite
        # Now compare against new value
        store2 = make_store(tmp_path)
        store2.assert_json("user", {"id": 1, "name": "Bob"})  # should pass

    def test_per_call_update_flag_overrides_store_flag(self, tmp_path):
        store = make_store(tmp_path, update=False)
        store.assert_json("snap", {"v": 1})  # create
        store.assert_json("snap", {"v": 2}, update=True)  # overwrite
        store.assert_json("snap", {"v": 2})  # should pass

    def test_ignore_removes_fields_from_comparison(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("ts", {"id": 1, "created_at": "2024-01-01"}, ignore=["created_at"])
        # Different timestamp — should still pass because it's ignored
        store.assert_json("ts", {"id": 1, "created_at": "2025-06-15"}, ignore=["created_at"])

    def test_ignore_works_on_nested_keys(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("nested", {"user": {"id": 1, "updated_at": "t1"}}, ignore=["updated_at"])
        store.assert_json("nested", {"user": {"id": 1, "updated_at": "t2"}}, ignore=["updated_at"])

    def test_non_ignored_change_still_raises(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("snap", {"id": 1, "name": "old"}, ignore=["ts"])
        with pytest.raises(SnapshotMismatchError):
            store.assert_json("snap", {"id": 2, "name": "old"}, ignore=["ts"])

    def test_different_snapshot_names_are_independent(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_json("a", {"v": 1})
        store.assert_json("b", {"v": 2})
        store.assert_json("a", {"v": 1})  # should pass
        store.assert_json("b", {"v": 2})  # should pass


class TestSnapshotStoreText:

    def test_creates_text_snapshot_on_first_call(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_text("response", "Hello World")
        assert (tmp_path / "snapshots" / "response.txt").exists()

    def test_passes_on_matching_text(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_text("t", "same text")
        store.assert_text("t", "same text")  # must pass

    def test_raises_on_text_mismatch(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_text("t", "original")
        with pytest.raises(SnapshotMismatchError):
            store.assert_text("t", "changed")

    def test_update_overwrites_text_snapshot(self, tmp_path):
        store = make_store(tmp_path)
        store.assert_text("t", "v1")
        store.assert_text("t", "v2", update=True)
        store.assert_text("t", "v2")  # should pass


class TestSnapshotMismatchError:

    def test_is_assertion_error(self):
        err = SnapshotMismatchError("snap", "diff text")
        assert isinstance(err, AssertionError)

    def test_stores_name(self):
        err = SnapshotMismatchError("my_snap", "diff")
        assert err.name == "my_snap"

    def test_stores_diff(self):
        err = SnapshotMismatchError("snap", "my diff")
        assert err.diff == "my diff"
