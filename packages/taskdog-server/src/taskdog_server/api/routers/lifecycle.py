"""Task lifecycle endpoints (status changes with time tracking)."""

from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter

from taskdog_server.api.audit_helpers import (
    capture_old_task,
    log_task_operation,
    serialize_audit_value,
)
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    LifecycleControllerDep,
    QueryControllerDep,
)
from taskdog_server.api.models.requests import FixActualTimesRequest
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@dataclass(frozen=True)
class LifecycleOperation:
    """Configuration for a lifecycle endpoint."""

    name: str
    description: str


OPERATIONS = [
    LifecycleOperation("start", "Start a task"),
    LifecycleOperation("complete", "Complete a task"),
    LifecycleOperation("pause", "Pause a task"),
    LifecycleOperation("cancel", "Cancel a task"),
    LifecycleOperation("reopen", "Reopen a task"),
]


def _create_lifecycle_endpoint(op: LifecycleOperation) -> None:
    """Create and register a lifecycle endpoint.

    Args:
        op: Operation configuration
    """

    @router.post(f"/{{task_id}}/{op.name}", response_model=TaskOperationResponse)
    def endpoint(
        task_id: int,
        controller: LifecycleControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> TaskOperationResponse:
        result = controller.execute_lifecycle(op.name, task_id)
        broadcaster.task_status_changed(
            result.task, result.old_status.value, client_name
        )

        log_task_operation(
            audit_controller,
            operation=f"{op.name}_task",
            task=result.task,
            client_name=client_name,
            old_values={"status": result.old_status.value},
            new_values={"status": result.task.status.value},
        )

        return TaskOperationResponse.from_dto(result.task)


# Generate all lifecycle endpoints
for _op in OPERATIONS:
    _create_lifecycle_endpoint(_op)


@router.post("/{task_id}/fix-actual", response_model=TaskOperationResponse)
def fix_actual_times(
    task_id: int,
    request: FixActualTimesRequest,
    controller: LifecycleControllerDep,
    query_controller: QueryControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Fix actual start/end timestamps and/or duration for a task.

    Used to correct timestamps after the fact, for historical accuracy.
    Past dates are allowed since these are historical records.

    Args:
        task_id: Task ID
        request: Fix actual times request with optional start/end/duration values
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with corrected timestamps/duration

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    # Get old values before update for audit trail
    old_task = capture_old_task(query_controller, task_id)

    # Determine values to pass (Ellipsis = keep current)
    actual_start = (
        None
        if request.clear_start
        else request.actual_start
        if request.actual_start is not None
        else ...
    )
    actual_end = (
        None
        if request.clear_end
        else request.actual_end
        if request.actual_end is not None
        else ...
    )
    actual_duration = (
        None
        if request.clear_duration
        else request.actual_duration
        if request.actual_duration is not None
        else ...
    )

    result = controller.fix_actual_times(
        task_id, actual_start, actual_end, actual_duration
    )

    # Broadcast event
    broadcaster.task_updated(
        result, ["actual_start", "actual_end", "actual_duration"], client_name
    )

    # Audit log with old/new values; actual_duration stays a string to preserve
    # the existing log format, datetimes go through the shared serializer.
    def _actual_values(task: Any) -> dict[str, Any]:
        return {
            "actual_start": serialize_audit_value(task.actual_start),
            "actual_end": serialize_audit_value(task.actual_end),
            "actual_duration": str(task.actual_duration)
            if task.actual_duration is not None
            else None,
        }

    log_task_operation(
        audit_controller,
        operation="fix_actual_times",
        task=result,
        client_name=client_name,
        old_values=_actual_values(old_task) if old_task else None,
        new_values=_actual_values(result),
    )

    return TaskOperationResponse.from_dto(result)
