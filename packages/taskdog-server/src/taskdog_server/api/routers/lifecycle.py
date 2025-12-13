"""Task lifecycle endpoints (status changes with time tracking)."""

from dataclasses import dataclass

from fastapi import APIRouter

from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    LifecycleControllerDep,
    QueryControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import FixActualTimesRequest
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@dataclass(frozen=True)
class LifecycleOperation:
    """Configuration for a lifecycle endpoint."""

    name: str
    old_status: str
    description: str
    returns: str


OPERATIONS = [
    LifecycleOperation("start", "PENDING", "Start a task", "actual_start timestamp"),
    LifecycleOperation(
        "complete", "IN_PROGRESS", "Complete a task", "actual_end timestamp"
    ),
    LifecycleOperation("pause", "IN_PROGRESS", "Pause a task", "cleared timestamps"),
    LifecycleOperation(
        "cancel", "IN_PROGRESS", "Cancel a task", "actual_end timestamp"
    ),
    LifecycleOperation("reopen", "COMPLETED", "Reopen a task", "cleared timestamps"),
]


def _create_lifecycle_endpoint(op: LifecycleOperation) -> None:
    """Create and register a lifecycle endpoint.

    Args:
        op: Operation configuration
    """

    @router.post(f"/{{task_id}}/{op.name}", response_model=TaskOperationResponse)
    @handle_task_errors
    async def endpoint(
        task_id: int,
        controller: LifecycleControllerDep,
        broadcaster: EventBroadcasterDep,
        audit_controller: AuditLogControllerDep,
        client_name: AuthenticatedClientDep,
    ) -> TaskOperationResponse:
        controller_method = getattr(controller, f"{op.name}_task")
        result = controller_method(task_id)
        broadcaster.task_status_changed(result, op.old_status, client_name)

        # Audit log
        audit_controller.log_operation(
            operation=f"{op.name}_task",
            resource_type="task",
            resource_id=task_id,
            resource_name=result.name,
            client_name=client_name,
            old_values={"status": op.old_status},
            new_values={"status": result.status.value},
            success=True,
        )

        return TaskOperationResponse.from_dto(result)

    endpoint.__name__ = f"{op.name}_task"
    endpoint.__doc__ = f"""{op.description} (change status and update timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with {op.returns}

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """


# Generate all lifecycle endpoints
for _op in OPERATIONS:
    _create_lifecycle_endpoint(_op)


@router.post("/{task_id}/fix-actual", response_model=TaskOperationResponse)
@handle_task_errors
async def fix_actual_times(
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
    try:
        old_task_output = query_controller.get_task_by_id(task_id)
        old_task = old_task_output.task if old_task_output else None
    except Exception:
        old_task = None

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

    # Audit log with old values
    old_values: dict[str, str | None] = {}
    if old_task:
        old_values["actual_start"] = (
            old_task.actual_start.isoformat() if old_task.actual_start else None
        )
        old_values["actual_end"] = (
            old_task.actual_end.isoformat() if old_task.actual_end else None
        )
        old_values["actual_duration"] = (
            str(old_task.actual_duration)
            if old_task.actual_duration is not None
            else None
        )

    audit_controller.log_operation(
        operation="fix_actual_times",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.name,
        client_name=client_name,
        old_values=old_values if old_values else None,
        new_values={
            "actual_start": result.actual_start.isoformat()
            if result.actual_start
            else None,
            "actual_end": result.actual_end.isoformat() if result.actual_end else None,
            "actual_duration": str(result.actual_duration)
            if result.actual_duration is not None
            else None,
        },
        success=True,
    )

    return TaskOperationResponse.from_dto(result)
