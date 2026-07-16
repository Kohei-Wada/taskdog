"""Task relationship endpoints (dependencies, tags)."""

from fastapi import APIRouter

from taskdog_server.api.audit_helpers import log_task_operation
from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    RelationshipControllerDep,
)
from taskdog_server.api.models.requests import (
    AddDependencyRequest,
    SetTaskTagsRequest,
)
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@router.post("/{task_id}/dependencies", response_model=TaskOperationResponse)
def add_dependency(
    task_id: int,
    request: AddDependencyRequest,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Add a dependency to a task.

    Args:
        task_id: Task ID that will depend on another task
        request: Dependency data (ID of task to depend on)
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with new dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails (e.g., circular dependency)
    """
    result = controller.add_dependency(task_id, request.depends_on_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["depends_on"], client_name)

    log_task_operation(
        audit_controller,
        operation="add_dependency",
        task=result,
        client_name=client_name,
        new_values={"added_dependency": request.depends_on_id},
    )

    return TaskOperationResponse.from_dto(result)


@router.delete(
    "/{task_id}/dependencies/{depends_on_id}", response_model=TaskOperationResponse
)
def remove_dependency(
    task_id: int,
    depends_on_id: int,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Remove a dependency from a task.

    Args:
        task_id: Task ID
        depends_on_id: ID of dependency to remove
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data without the dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.remove_dependency(task_id, depends_on_id)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["depends_on"], client_name)

    log_task_operation(
        audit_controller,
        operation="remove_dependency",
        task=result,
        client_name=client_name,
        old_values={"removed_dependency": depends_on_id},
    )

    return TaskOperationResponse.from_dto(result)


@router.put("/{task_id}/tags", response_model=TaskOperationResponse)
def set_task_tags(
    task_id: int,
    request: SetTaskTagsRequest,
    controller: RelationshipControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> TaskOperationResponse:
    """Set task tags (replaces existing tags).

    Args:
        task_id: Task ID
        request: New tags list
        controller: Relationship controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (for broadcast payload)

    Returns:
        Updated task data with new tags

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.set_task_tags(task_id, request.tags)

    # Broadcast WebSocket event in background
    broadcaster.task_updated(result, ["tags"], client_name)

    log_task_operation(
        audit_controller,
        operation="set_tags",
        task=result,
        client_name=client_name,
        new_values={"tags": list(result.tags)},
    )

    return TaskOperationResponse.from_dto(result)
