"""Task relationship endpoints (dependencies, tags, hours logging)."""

from fastapi import APIRouter

from taskdog_server.api.dependencies import (
    AuthenticatedClientDep,
    EventBroadcasterDep,
    RelationshipControllerDep,
    TimeProviderDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import (
    AddDependencyRequest,
    LogHoursRequest,
    SetTaskTagsRequest,
)
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@router.post("/{task_id}/dependencies", response_model=TaskOperationResponse)
@handle_task_errors
async def add_dependency(
    task_id: int,
    request: AddDependencyRequest,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Add a dependency to a task.

    Args:
        task_id: Task ID that will depend on another task
        request: Dependency data (ID of task to depend on)
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with new dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails (e.g., circular dependency)
    """
    result = controller.add_dependency(task_id, request.depends_on_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["depends_on"], client_name)

    return TaskOperationResponse.from_dto(result)


@router.delete(
    "/{task_id}/dependencies/{depends_on_id}", response_model=TaskOperationResponse
)
@handle_task_errors
async def remove_dependency(
    task_id: int,
    depends_on_id: int,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Remove a dependency from a task.

    Args:
        task_id: Task ID
        depends_on_id: ID of dependency to remove
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data without the dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.remove_dependency(task_id, depends_on_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["depends_on"], client_name)

    return TaskOperationResponse.from_dto(result)


@router.put("/{task_id}/tags", response_model=TaskOperationResponse)
@handle_task_errors
async def set_task_tags(
    task_id: int,
    request: SetTaskTagsRequest,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Set task tags (replaces existing tags).

    Args:
        task_id: Task ID
        request: New tags list
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with new tags

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.set_task_tags(task_id, request.tags)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["tags"], client_name)

    return TaskOperationResponse.from_dto(result)


@router.post("/{task_id}/log-hours", response_model=TaskOperationResponse)
@handle_task_errors
async def log_hours(
    task_id: int,
    request: LogHoursRequest,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    time_provider: TimeProviderDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Log actual hours worked on a task for a specific date.

    Args:
        task_id: Task ID
        request: Hours and date data
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        time_provider: Time provider dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with logged hours

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    log_date = request.date if request.date else time_provider.today()
    result = controller.log_hours(task_id, request.hours, log_date.isoformat())

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["actual_daily_hours"], client_name)

    return TaskOperationResponse.from_dto(result)
