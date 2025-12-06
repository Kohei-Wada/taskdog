"""Task lifecycle endpoints (status changes with time tracking)."""

from dataclasses import dataclass

from fastapi import APIRouter

from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    LifecycleControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
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
