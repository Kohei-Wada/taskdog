"""Tests for SqliteAuditLogRepository.get_deadline_changes."""

from datetime import datetime
from pathlib import Path

import pytest

from taskdog_core.domain.entities.audit_log import AuditLog
from taskdog_core.infrastructure.persistence.database.models.task_model import Base
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)


class TestGetDeadlineChanges:
    """Test cases for get_deadline_changes."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up a repository with a temporary database."""
        db_path = Path(tmp_path) / "test_audit.db"
        self.repository = SqliteAuditLogRepository(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.repository.engine)
        yield
        self.repository.close()

    def _save(
        self,
        *,
        operation: str = "update_task",
        old_values: dict | None,
        new_values: dict | None,
        timestamp: datetime = datetime(2026, 7, 14, 10, 0),
        success: bool = True,
        task_id: int = 1,
    ) -> None:
        self.repository.save(
            AuditLog(
                timestamp=timestamp,
                operation=operation,
                resource_type="task",
                success=success,
                resource_id=task_id,
                resource_name="task",
                old_values=old_values,
                new_values=new_values,
            )
        )

    def test_returns_deadline_changes(self) -> None:
        self._save(
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-25T18:00:00"},
        )

        changes = self.repository.get_deadline_changes()

        assert len(changes) == 1
        assert changes[0].old_values == {"deadline": "2026-07-20T18:00:00"}
        assert changes[0].new_values == {"deadline": "2026-07-25T18:00:00"}

    def test_includes_initial_setting_and_removal(self) -> None:
        self._save(
            old_values={"deadline": None},
            new_values={"deadline": "2026-07-20T18:00:00"},
        )
        self._save(
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": None},
        )

        changes = self.repository.get_deadline_changes()

        assert len(changes) == 2

    def test_ignores_updates_without_deadline_change(self) -> None:
        self._save(old_values={"name": "a"}, new_values={"name": "b"})
        self._save(
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-20T18:00:00"},
        )
        self._save(old_values=None, new_values=None)

        assert self.repository.get_deadline_changes() == []

    def test_ignores_other_operations_and_failures(self) -> None:
        self._save(
            operation="optimize_schedule",
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-25T18:00:00"},
        )
        self._save(
            success=False,
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-25T18:00:00"},
        )

        assert self.repository.get_deadline_changes() == []

    def test_since_filters_by_timestamp(self) -> None:
        self._save(
            old_values={"deadline": "2026-07-01T18:00:00"},
            new_values={"deadline": "2026-07-02T18:00:00"},
            timestamp=datetime(2026, 6, 1, 10, 0),
        )
        self._save(
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-25T18:00:00"},
            timestamp=datetime(2026, 7, 14, 10, 0),
        )

        changes = self.repository.get_deadline_changes(since=datetime(2026, 7, 1))

        assert len(changes) == 1
        assert changes[0].timestamp == datetime(2026, 7, 14, 10, 0)

    def test_returns_oldest_first(self) -> None:
        self._save(
            old_values={"deadline": "2026-07-20T18:00:00"},
            new_values={"deadline": "2026-07-25T18:00:00"},
            timestamp=datetime(2026, 7, 14, 10, 0),
        )
        self._save(
            old_values={"deadline": "2026-07-01T18:00:00"},
            new_values={"deadline": "2026-07-02T18:00:00"},
            timestamp=datetime(2026, 6, 1, 10, 0),
        )

        changes = self.repository.get_deadline_changes()

        assert [c.timestamp for c in changes] == [
            datetime(2026, 6, 1, 10, 0),
            datetime(2026, 7, 14, 10, 0),
        ]
