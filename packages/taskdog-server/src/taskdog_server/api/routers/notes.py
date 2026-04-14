"""Task notes endpoints (CRUD operations for markdown notes)."""

from fastapi import APIRouter, status

from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    NotesControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import UpdateNotesRequest
from taskdog_server.api.models.responses import NotesResponse

router = APIRouter()


@router.get("/{task_id}/notes", response_model=NotesResponse)
@handle_task_errors
async def get_task_notes(
    task_id: int,
    controller: NotesControllerDep,
    _client_name: AuthenticatedClientDep,
) -> NotesResponse:
    """Get task notes.

    Args:
        task_id: Task ID
        controller: Notes controller dependency

    Returns:
        Notes content and metadata

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.get_notes(task_id)
    return NotesResponse(
        task_id=result.task_id, content=result.content, has_notes=result.has_notes
    )


@router.put("/{task_id}/notes", response_model=NotesResponse)
@handle_task_errors
async def update_task_notes(
    task_id: int,
    request: UpdateNotesRequest,
    controller: NotesControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> NotesResponse:
    """Update task notes.

    Args:
        task_id: Task ID
        request: Notes content
        controller: Notes controller dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (used for broadcast exclusion)

    Returns:
        Updated notes content and metadata

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.update_notes(task_id, request.content)

    # Broadcast WebSocket event in background (exclude the requester by client name)
    broadcaster.task_notes_updated(task_id, result.task_name, client_name)

    # Audit log
    audit_controller.log_operation(
        operation="update_notes",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.task_name,
        client_name=client_name,
        new_values={"has_notes": result.has_notes},
        success=True,
    )

    return NotesResponse(
        task_id=result.task_id, content=result.content, has_notes=result.has_notes
    )


@router.delete("/{task_id}/notes", status_code=status.HTTP_204_NO_CONTENT)
@handle_task_errors
async def delete_task_notes(
    task_id: int,
    controller: NotesControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> None:
    """Delete task notes.

    Args:
        task_id: Task ID
        controller: Notes controller dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (used for broadcast exclusion)

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.delete_notes(task_id)

    # Broadcast WebSocket event in background (exclude the requester by client name)
    broadcaster.task_notes_updated(task_id, result.task_name, client_name)

    # Audit log
    audit_controller.log_operation(
        operation="delete_notes",
        resource_type="task",
        resource_id=task_id,
        resource_name=result.task_name,
        client_name=client_name,
        success=True,
    )
