"""Tests for the backup/restore endpoints (issue #999)."""

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from taskdog_core.controllers.backup_controller import BackupController
from taskdog_core.infrastructure.persistence.database.sqlite_backup_store import (
    SqliteBackupStore,
)
from taskdog_server.api.error_handlers import register_exception_handlers
from taskdog_server.api.routers import backup_router
from taskdog_server.config.server_config_manager import AuthConfig, ServerConfig


def _seed_db(path: Path, rows: list[str]) -> None:
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


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    db = tmp_path / "tasks.db"
    _seed_db(db, ["alpha", "beta"])
    return db


@pytest.fixture
def client(db_path: Path) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    class _Ctx:
        backup_controller = BackupController(SqliteBackupStore(f"sqlite:///{db_path}"))

    app.state.api_context = _Ctx()
    app.state.server_config = ServerConfig(auth=AuthConfig(enabled=False))
    app.include_router(backup_router, prefix="/api/v1", tags=["backup"])
    return TestClient(app)


class TestBackupEndpoint:
    def test_backup_streams_a_valid_snapshot(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        response = client.get("/api/v1/backup")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment" in response.headers["content-disposition"]
        assert ".db" in response.headers["content-disposition"]

        downloaded = tmp_path / "downloaded.db"
        downloaded.write_bytes(response.content)
        assert _read_rows(downloaded) == ["alpha", "beta"]


class TestRestoreEndpoint:
    def test_restore_stages_a_valid_upload(
        self, client: TestClient, tmp_path: Path, db_path: Path
    ) -> None:
        snapshot = tmp_path / "snapshot.db"
        _seed_db(snapshot, ["restored"])

        response = client.post(
            "/api/v1/restore",
            files={
                "file": ("backup.db", snapshot.read_bytes(), "application/octet-stream")
            },
        )

        assert response.status_code == 200
        assert response.json() == {"status": "pending", "message": "restart required"}
        # Staged, not yet applied.
        assert db_path.with_name("tasks.db.pending-restore").exists()
        assert _read_rows(db_path) == ["alpha", "beta"]

    def test_restore_rejects_invalid_upload(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/restore",
            files={"file": ("bad.db", b"not a database", "application/octet-stream")},
        )

        assert response.status_code == 400
