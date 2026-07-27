"""Snapshot-based response assertion helpers."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SnapshotMismatchError(AssertionError):
    """Raised when a response body does not match its stored snapshot."""

    def __init__(self, name: str, diff: str) -> None:
        self.name = name
        self.diff = diff
        super().__init__(f"Snapshot '{name}' mismatch:\n{diff}")


def _redact(obj: Any, ignore: Optional[List[str]]) -> Any:
    """Return *obj* with every key listed in *ignore* replaced by ``'<ignored>'``.

    Works recursively on dicts and lists.
    """
    if not ignore:
        return obj
    if isinstance(obj, dict):
        return {
            k: "<ignored>" if k in ignore else _redact(v, ignore)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(item, ignore) for item in obj]
    return obj


class SnapshotStore:
    """Manages JSON and text snapshots on disk.

    Snapshots are stored as ``{name}.json`` (or ``{name}.txt``) files
    under *snapshot_dir*.  On first run (or when *update* is ``True``)
    the current value is written to disk; on subsequent runs it is read
    back and compared.

    Args:
        snapshot_dir: Directory where snapshot files are stored.
            Defaults to ``".lashtest_snapshots"`` in the current
            working directory.
        update: When ``True`` every call to :meth:`assert_json` /
            :meth:`assert_text` overwrites the stored snapshot instead
            of comparing.  Useful for bulk-updating snapshots after an
            intentional API change.  Defaults to ``False``.

    Example::

        from lashtest import APIClient
        from lashtest.assertions.snapshot import SnapshotStore

        snapshots = SnapshotStore()

        def test_user_profile():
            with APIClient('https://api.example.com').get('/users/1') as r:
                snapshots.assert_json(
                    'user_profile',
                    r.json(),
                    ignore=['updated_at', 'created_at'],
                )
    """

    def __init__(
        self,
        snapshot_dir: Union[str, Path] = ".lashtest_snapshots",
        *,
        update: bool = False,
    ) -> None:
        self.snapshot_dir = Path(snapshot_dir)
        self.update = update

    def _path(self, name: str, ext: str) -> Path:
        return self.snapshot_dir / f"{name}.{ext}"

    def _ensure_dir(self) -> None:
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    # ── JSON snapshots ────────────────────────────────────────────────────────

    def assert_json(
        self,
        name: str,
        actual: Any,
        *,
        ignore: Optional[List[str]] = None,
        update: Optional[bool] = None,
    ) -> None:
        """Assert that *actual* matches the stored JSON snapshot *name*.

        Args:
            name: Snapshot identifier (used as the file stem).
            actual: The value to snapshot (must be JSON-serialisable).
            ignore: List of dict keys to exclude from the comparison.
                The keys are redacted recursively throughout the whole
                document before comparison, so timestamps or dynamic IDs
                can be safely ignored.
            update: Override the store-level *update* flag for this call.

        Raises:
            SnapshotMismatchError: When the sanitised *actual* does not
                match the stored snapshot (and *update* is ``False``).
        """
        path = self._path(name, "json")
        do_update = update if update is not None else self.update

        sanitised = _redact(actual, ignore)

        if do_update or not path.exists():
            self._ensure_dir()
            path.write_text(json.dumps(sanitised, indent=2, sort_keys=True), encoding="utf-8")
            return

        stored_raw = path.read_text(encoding="utf-8")
        stored = json.loads(stored_raw)

        if stored != sanitised:
            import difflib
            stored_lines = json.dumps(stored, indent=2, sort_keys=True).splitlines(keepends=True)
            actual_lines = json.dumps(sanitised, indent=2, sort_keys=True).splitlines(keepends=True)
            diff = "".join(
                difflib.unified_diff(stored_lines, actual_lines, fromfile="stored", tofile="actual")
            )
            raise SnapshotMismatchError(name, diff)

    # ── text snapshots ────────────────────────────────────────────────────────

    def assert_text(
        self,
        name: str,
        actual: str,
        *,
        update: Optional[bool] = None,
    ) -> None:
        """Assert that *actual* matches the stored plain-text snapshot *name*.

        Args:
            name: Snapshot identifier.
            actual: The text to snapshot.
            update: Override the store-level *update* flag for this call.

        Raises:
            SnapshotMismatchError: When *actual* does not match the stored snapshot.
        """
        path = self._path(name, "txt")
        do_update = update if update is not None else self.update

        if do_update or not path.exists():
            self._ensure_dir()
            path.write_text(actual, encoding="utf-8")
            return

        stored = path.read_text(encoding="utf-8")
        if stored != actual:
            import difflib
            stored_lines = stored.splitlines(keepends=True)
            actual_lines = actual.splitlines(keepends=True)
            diff = "".join(
                difflib.unified_diff(stored_lines, actual_lines, fromfile="stored", tofile="actual")
            )
            raise SnapshotMismatchError(name, diff)
