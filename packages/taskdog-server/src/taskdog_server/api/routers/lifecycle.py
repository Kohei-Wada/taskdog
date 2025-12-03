"""Task lifecycle endpoints (status changes with time tracking)."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Header

from taskdog_server.api.dependencies import EventBroadcasterDep, LifecycleControllerDep
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
        x_client_id: Annotated[str | None, Header()] = None,
        x_user_name: Annotated[str | None, Header()] = None,
    ) -> TaskOperationResponse:
        controller_method = getattr(controller, f"{op.name}_task")
        result = controller_method(task_id)
        broadcaster.task_status_changed(result, op.old_status, x_client_id, x_user_name)
        return TaskOperationResponse.from_dto(result)

    endpoint.__name__ = f"{op.name}_task"
    endpoint.__doc__ = f"""{op.description} (change status and update timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with {op.returns}

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """


# Generate all lifecycle endpoints
for _op in OPERATIONS:
    _create_lifecycle_endpoint(_op)
