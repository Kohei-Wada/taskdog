"""Presenter for converting AuditLogListOutput DTO to AuditLogViewModel.

This presenter owns the audit-log *mapping* logic: selecting which fields
changed between old and new values and formatting each value for display. It
is free of rendering-technology dependencies (no Rich, no Textual) so it can
be used from both the CLI and the TUI.
"""

from typing import Any

from taskdog.view_models.audit_log_view_model import (
    AuditChangeViewModel,
    AuditLogRowViewModel,
    AuditLogViewModel,
)
from taskdog_core.application.dto.audit_log_dto import (
    AuditLogListOutput,
    AuditLogOutput,
)

MAX_VALUE_LENGTH = 15


class AuditLogPresenter:
    """Convert AuditLogListOutput DTO to AuditLogViewModel."""

    def present(self, output: AuditLogListOutput) -> AuditLogViewModel:
        return AuditLogViewModel(
            rows=tuple(self._map_row(log) for log in output.logs),
            total_count=output.total_count,
        )

    def _map_row(self, log: AuditLogOutput) -> AuditLogRowViewModel:
        return AuditLogRowViewModel(
            id=log.id,
            timestamp=log.timestamp,
            operation=log.operation,
            client_name=log.client_name,
            resource_id=log.resource_id,
            resource_name=log.resource_name,
            success=log.success,
            error_message=log.error_message,
            changes=self._compute_changes(log.old_values, log.new_values),
        )

    def _compute_changes(
        self,
        old_values: dict[str, Any] | None,
        new_values: dict[str, Any] | None,
    ) -> tuple[AuditChangeViewModel, ...]:
        all_keys: set[str] = set()
        if old_values:
            all_keys.update(old_values.keys())
        if new_values:
            all_keys.update(new_values.keys())

        changes: list[AuditChangeViewModel] = []
        for key in sorted(all_keys):
            old_val = old_values.get(key) if old_values else None
            new_val = new_values.get(key) if new_values else None
            if old_val != new_val:
                changes.append(
                    AuditChangeViewModel(
                        key=key,
                        old=self._format_value(old_val),
                        new=self._format_value(new_val),
                    )
                )
        return tuple(changes)

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "∅"
        if isinstance(value, bool):
            return "✓" if value else "✗"
        if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
            return value[:MAX_VALUE_LENGTH] + "..."
        return str(value)
