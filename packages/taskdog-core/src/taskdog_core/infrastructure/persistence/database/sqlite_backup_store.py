"""SQLite implementation of the backup/restore port."""

import os
import sqlite3
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from taskdog_core.domain.exceptions.backup_exceptions import (
    BackupNotSupportedError,
    BackupValidationError,
)
from taskdog_core.domain.services.backup_store import IBackupStore

# Stream the snapshot in 1 MiB chunks.
_CHUNK_SIZE = 1024 * 1024


class SqliteBackupStore(IBackupStore):
    """Backup/restore a SQLite database file.

    The only place in the codebase that knows about VACUUM INTO, integrity
    checks, WAL sidecars, and the on-disk file swap.
    """

    def __init__(self, database_url: str) -> None:
        """Initialize from a SQLAlchemy database URL.

        Args:
            database_url: e.g. "sqlite:////home/user/.local/share/taskdog/tasks.db".
                In-memory databases have no file and are not supported.
        """
        database = make_url(database_url).database
        # ":memory:", empty, or None all denote a non-file (in-memory) store.
        self._db_path: Path | None = (
            Path(database) if database and database != ":memory:" else None
        )

    @property
    def _pending_path(self) -> Path:
        assert self._db_path is not None
        return self._db_path.with_name(self._db_path.name + ".pending-restore")

    def _sidecar(self, suffix: str) -> Path:
        assert self._db_path is not None
        return self._db_path.with_name(self._db_path.name + suffix)

    def _require_file_store(self) -> Path:
        if self._db_path is None:
            raise BackupNotSupportedError(
                "Backup/restore is only supported for file-based SQLite databases."
            )
        return self._db_path

    def create_snapshot(self) -> Iterator[bytes]:
        """Stream a consistent, defragmented single-file snapshot.

        ``VACUUM INTO`` yields a transactionally consistent copy with no WAL
        sidecars. The temp file is always removed once streaming finishes.
        """
        db_path = self._require_file_store()

        # VACUUM INTO requires the target not to exist, so reserve a name and
        # delete the placeholder before handing it to SQLite.
        fd, tmp_name = tempfile.mkstemp(suffix=".db", dir=db_path.parent)
        os.close(fd)
        tmp_path = Path(tmp_name)
        tmp_path.unlink()

        def _stream() -> Iterator[bytes]:
            try:
                conn = sqlite3.connect(db_path)
                try:
                    conn.execute("VACUUM main INTO ?", (str(tmp_path),))
                finally:
                    conn.close()

                with tmp_path.open("rb") as snapshot:
                    while chunk := snapshot.read(_CHUNK_SIZE):
                        yield chunk
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        return _stream()

    def stage_restore(self, data: Iterator[bytes]) -> None:
        """Write the upload to staging and validate it before accepting."""
        db_path = self._require_file_store()
        pending = self._pending_path

        with pending.open("wb") as staged:
            for chunk in data:
                staged.write(chunk)

        if not self._is_valid_sqlite(pending):
            pending.unlink(missing_ok=True)
            raise BackupValidationError(
                "Uploaded file is not a valid SQLite database (integrity check failed)."
            )

        # Keep mypy/readers honest that db_path is the swap target at apply time.
        assert db_path == self._db_path

    @staticmethod
    def _is_valid_sqlite(path: Path) -> bool:
        try:
            conn = sqlite3.connect(path)
            try:
                row = conn.execute("PRAGMA integrity_check").fetchone()
            finally:
                conn.close()
        except sqlite3.DatabaseError:
            return False
        return row is not None and row[0] == "ok"

    def apply_pending_restore(self) -> bool:
        """Swap a staged snapshot onto the live DB. Safe to call at startup."""
        if self._db_path is None:
            return False
        pending = self._pending_path
        if not pending.exists():
            return False

        db_path = self._db_path
        if db_path.exists():
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            db_path.replace(db_path.with_name(f"{db_path.name}.pre-restore-{ts}"))

        # Drop stale WAL/SHM so the old journal cannot shadow the restored DB.
        for suffix in ("-wal", "-shm"):
            self._sidecar(suffix).unlink(missing_ok=True)

        pending.replace(db_path)
        return True
