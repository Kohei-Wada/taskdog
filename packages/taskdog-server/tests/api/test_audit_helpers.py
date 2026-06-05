"""Tests for shared audit logging helpers."""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.api.audit_helpers import (
    capture_old_task,
    diff_task_fields,
    log_task_operation,
    serialize_audit_value,
)


class TestSerializeAuditValue:
    def test_enum_uses_value(self):
        assert serialize_audit_value(TaskStatus.IN_PROGRESS) == "IN_PROGRESS"

    def test_datetime_uses_isoformat(self):
        dt = datetime(2026, 1, 2, 18, 0, 0)
        assert serialize_audit_value(dt) == dt.isoformat()

    def test_dict_keys_and_values_serialized(self):
        d = {date(2026, 1, 2): 3.0}
        assert serialize_audit_value(d) == {"2026-01-02": 3.0}

    def test_primitive_passthrough(self):
        assert serialize_audit_value(5) == 5
        assert serialize_audit_value("x") == "x"
        assert serialize_audit_value(None) is None


class TestCaptureOldTask:
    def test_returns_task_when_present(self):
        task = SimpleNamespace(id=1, name="t")
        qc = MagicMock()
        qc.get_task_by_id.return_value = SimpleNamespace(task=task)
        assert capture_old_task(qc, 1) is task

    def test_returns_none_when_output_task_is_none(self):
        qc = MagicMock()
        qc.get_task_by_id.return_value = SimpleNamespace(task=None)
        assert capture_old_task(qc, 1) is None

    def test_returns_none_on_exception(self):
        qc = MagicMock()
        qc.get_task_by_id.side_effect = RuntimeError("boom")
        assert capture_old_task(qc, 1) is None


class TestDiffTaskFields:
    def test_serializes_old_and_new_for_changed_fields(self):
        old = SimpleNamespace(name="old", priority=1)
        new = SimpleNamespace(name="new", priority=2)
        old_values, new_values = diff_task_fields(old, new, ["name", "priority"])
        assert old_values == {"name": "old", "priority": 1}
        assert new_values == {"name": "new", "priority": 2}

    def test_skips_missing_attributes(self):
        old = SimpleNamespace(name="old")
        new = SimpleNamespace(name="new")
        old_values, new_values = diff_task_fields(old, new, ["name", "ghost"])
        assert old_values == {"name": "old"}
        assert new_values == {"name": "new"}

    def test_serializes_enum_and_datetime(self):
        dt = datetime(2026, 1, 2, 18, 0, 0)
        old = SimpleNamespace(status=TaskStatus.PENDING, planned_start=None)
        new = SimpleNamespace(status=TaskStatus.IN_PROGRESS, planned_start=dt)
        old_values, new_values = diff_task_fields(old, new, ["status", "planned_start"])
        assert old_values == {"status": "PENDING", "planned_start": None}
        assert new_values == {"status": "IN_PROGRESS", "planned_start": dt.isoformat()}

    def test_returns_none_for_empty_result(self):
        old = SimpleNamespace()
        new = SimpleNamespace()
        assert diff_task_fields(old, new, []) == (None, None)

    def test_returns_none_when_old_is_none(self):
        new = SimpleNamespace(name="new")
        assert diff_task_fields(None, new, ["name"]) == (None, None)


class TestLogTaskOperation:
    def test_defaults_task_resource_fields(self):
        audit = MagicMock()
        task = SimpleNamespace(id=7, name="Task 7")
        log_task_operation(
            audit,
            operation="create_task",
            task=task,
            client_name="cli",
            new_values={"name": "Task 7"},
        )
        audit.log_operation.assert_called_once_with(
            operation="create_task",
            resource_type="task",
            resource_id=7,
            resource_name="Task 7",
            client_name="cli",
            old_values=None,
            new_values={"name": "Task 7"},
            success=True,
        )
