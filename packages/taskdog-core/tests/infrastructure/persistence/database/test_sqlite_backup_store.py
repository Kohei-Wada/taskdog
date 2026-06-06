"""Tests for SqliteBackupStore (issue #999)."""

import sqlite3
from pathlib import Path

import pytest

from taskdog_core.domain.exceptions.backup_exceptions import (
    BackupNotSupportedError,
    BackupValidationError,
)
from taskdog_core.infrastructure.persistence.database.sqlite_backup_store import (
    SqliteBackupStore,
)


def _seed_db(path: Path, rows: list[str]) -> None:
    """Create a SQLite db at path with a notes table holding the given rows."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE notes (body TEXT)")
        conn.executemany("INSERT INTO notes (body) VALUES (?)", [(r,) for r in rows])
        conn.commit()
    finally:
        conn.close()


def _read_rows(path: Path) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return [row[0] for row in conn.execute("SELECT body FROM notes ORDER BY body")]
    finally:
        conn.close()


def _url(path: Path) -> str:
    return f"sqlite:///{path}"


class TestCreateSnapshot:
    def test_snapshot_round_trips(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["alpha", "beta"])
        store = SqliteBackupStore(_url(db))

        snapshot = tmp_path / "snapshot.db"
        with snapshot.open("wb") as out:
            for chunk in store.create_snapshot():
                out.write(chunk)

        assert _read_rows(snapshot) == ["alpha", "beta"]

    def test_snapshot_leaves_no_temp_files(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["x"])
        store = SqliteBackupStore(_url(db))

        list(store.create_snapshot())  # fully drain the stream

        assert [p.name for p in tmp_path.iterdir()] == ["tasks.db"]

    def test_in_memory_is_not_supported(self) -> None:
        store = SqliteBackupStore("sqlite:///:memory:")
        with pytest.raises(BackupNotSupportedError):
            list(store.create_snapshot())


class TestStageRestore:
    def test_invalid_upload_rejected_and_cleaned_up(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["keep"])
        store = SqliteBackupStore(_url(db))

        with pytest.raises(BackupValidationError):
            store.stage_restore(iter([b"this is not a sqlite database"]))

        # The live DB is untouched and no staging file is left behind.
        assert _read_rows(db) == ["keep"]
        assert not (tmp_path / "tasks.db.pending-restore").exists()

    def test_valid_upload_is_staged(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["old"])
        other = tmp_path / "other.db"
        _seed_db(other, ["new"])
        store = SqliteBackupStore(_url(db))

        store.stage_restore(iter([other.read_bytes()]))

        # Staged, not yet applied.
        assert (tmp_path / "tasks.db.pending-restore").exists()
        assert _read_rows(db) == ["old"]


class TestApplyPendingRestore:
    def test_no_pending_returns_false(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["only"])
        store = SqliteBackupStore(_url(db))

        assert store.apply_pending_restore() is False

    def test_pending_is_applied_with_wal_cleanup(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        _seed_db(db, ["old"])
        # Stale WAL/SHM sidecars must be removed so they can't shadow the restore.
        (tmp_path / "tasks.db-wal").write_bytes(b"stale-wal")
        (tmp_path / "tasks.db-shm").write_bytes(b"stale-shm")

        snapshot = tmp_path / "snapshot.db"
        _seed_db(snapshot, ["restored"])
        store = SqliteBackupStore(_url(db))
        store.stage_restore(iter([snapshot.read_bytes()]))

        assert store.apply_pending_restore() is True

        assert _read_rows(db) == ["restored"]
        assert not (tmp_path / "tasks.db.pending-restore").exists()
        assert not (tmp_path / "tasks.db-wal").exists()
        assert not (tmp_path / "tasks.db-shm").exists()
        # Previous DB preserved as a pre-restore copy.
        pre_restore = list(tmp_path.glob("tasks.db.pre-restore-*"))
        assert len(pre_restore) == 1
        assert _read_rows(pre_restore[0]) == ["old"]
