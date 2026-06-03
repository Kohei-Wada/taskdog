"""Tests for AuditLogPresenter."""

from datetime import datetime

from taskdog.presenters.audit_log_presenter import AuditLogPresenter
from taskdog.view_models.audit_log_view_model import (
    AuditChangeViewModel,
    AuditLogRowViewModel,
    AuditLogViewModel,
)
from taskdog_core.application.dto.audit_log_dto import (
    AuditLogListOutput,
    AuditLogOutput,
)


def _log(**overrides) -> AuditLogOutput:
    defaults = {
        "id": 1,
        "timestamp": datetime(2025, 1, 2, 3, 4, 5),
        "client_name": "claude-code",
        "operation": "update_task",
        "resource_type": "task",
        "resource_id": 42,
        "resource_name": "Some task",
        "old_values": None,
        "new_values": None,
        "success": True,
        "error_message": None,
    }
    defaults.update(overrides)
    return AuditLogOutput(**defaults)


class TestAuditLogPresenter:
    def test_passes_through_scalar_fields(self):
        out = AuditLogListOutput(logs=[_log()], total_count=7)
        vm = AuditLogPresenter().present(out)

        assert isinstance(vm, AuditLogViewModel)
        assert vm.total_count == 7
        assert len(vm.rows) == 1
        row = vm.rows[0]
        assert isinstance(row, AuditLogRowViewModel)
        assert row.id == 1
        assert row.timestamp == datetime(2025, 1, 2, 3, 4, 5)
        assert row.operation == "update_task"
        assert row.client_name == "claude-code"
        assert row.resource_id == 42
        assert row.resource_name == "Some task"
        assert row.success is True
        assert row.error_message is None

    def test_no_values_yields_empty_changes(self):
        vm = AuditLogPresenter().present(
            AuditLogListOutput(logs=[_log(old_values=None, new_values=None)])
        )
        assert vm.rows[0].changes == ()

    def test_only_changed_keys_are_included_and_sorted(self):
        vm = AuditLogPresenter().present(
            AuditLogListOutput(
                logs=[
                    _log(
                        old_values={"priority": 3, "name": "a", "same": 1},
                        new_values={"priority": 5, "name": "b", "same": 1},
                    )
                ]
            )
        )
        changes = vm.rows[0].changes
        assert changes == (
            AuditChangeViewModel(key="name", old="a", new="b"),
            AuditChangeViewModel(key="priority", old="3", new="5"),
        )

    def test_key_present_on_one_side_only(self):
        vm = AuditLogPresenter().present(
            AuditLogListOutput(logs=[_log(old_values=None, new_values={"tags": ["x"]})])
        )
        assert vm.rows[0].changes == (
            AuditChangeViewModel(key="tags", old="∅", new="['x']"),
        )

    def test_value_formatting_none_bool_and_long_string(self):
        long = "x" * 20
        vm = AuditLogPresenter().present(
            AuditLogListOutput(
                logs=[
                    _log(
                        old_values={"a": None, "b": True, "c": "short", "d": long},
                        new_values={"a": 1, "b": False, "c": "short", "d": "y"},
                    )
                ]
            )
        )
        changes = {c.key: (c.old, c.new) for c in vm.rows[0].changes}
        assert changes["a"] == ("∅", "1")
        assert changes["b"] == ("✓", "✗")
        assert "c" not in changes  # unchanged
        assert changes["d"] == ("x" * 15 + "...", "y")
