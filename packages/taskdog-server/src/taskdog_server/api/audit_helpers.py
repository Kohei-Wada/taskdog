"""Shared helpers for audit logging in API routers.

Consolidates the audit-log boilerplate that was repeated across routers:
value serialization, capturing pre-change task state, diffing changed fields,
and the task-resource ``log_operation`` call.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from taskdog_core.controllers.audit_log_controller import AuditLogController
    from taskdog_core.controllers.query_controller import QueryController


def serialize_audit_value(val: object) -> object:
    """Serialize a value for JSON-safe audit logging."""
    if hasattr(val, "value"):
        val = val.value
    if isinstance(val, datetime):
        val = val.isoformat()
    if isinstance(val, dict):
        val = {
            k.isoformat() if isinstance(k, (date, datetime)) else k: (
                v.isoformat() if isinstance(v, (date, datetime)) else v
            )
            for k, v in val.items()
        }
    return val


def capture_old_task(query_controller: "QueryController", task_id: int) -> Any:
    """Fetch a task's pre-change state for the audit trail.

    Returns the task detail DTO, or ``None`` if it cannot be retrieved, so the
    caller can still log the operation without old values.
    """
    try:
        output = query_controller.get_task_by_id(task_id)
        return output.task if output else None
    except Exception:
        return None


def diff_task_fields(
    old_task: Any, new_task: Any, fields: list[str]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Build serialized old/new value dicts for the given fields.

    Skips fields absent on either side. Returns ``(None, None)`` when there is
    nothing to record (no old task, or no matching fields).
    """
    old_values: dict[str, Any] = {}
    new_values: dict[str, Any] = {}
    if old_task is not None:
        for field in fields:
            if hasattr(old_task, field) and hasattr(new_task, field):
                old_values[field] = serialize_audit_value(getattr(old_task, field))
                new_values[field] = serialize_audit_value(getattr(new_task, field))
    return old_values or None, new_values or None


def log_task_operation(
    audit_controller: "AuditLogController",
    *,
    operation: str,
    task: Any,
    client_name: str | None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> None:
    """Log a successful ``task``-resource operation with task id/name defaults."""
    audit_controller.log_operation(
        operation=operation,
        resource_type="task",
        resource_id=task.id,
        resource_name=task.name,
        client_name=client_name,
        old_values=old_values,
        new_values=new_values,
        success=True,
    )
