"""Task notes endpoints (CRUD operations for markdown notes)."""

from fastapi import APIRouter, status

from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    NotesControllerDep,
)
from taskdog_server.api.models.requests import AppendNotesRequest, UpdateNotesRequest
from taskdog_server.api.models.responses import NotesResponse
from taskdog_server.api.validators import MAX_NOTES_LENGTH

router = APIRouter()


@router.get("/{task_id}/notes", response_model=NotesResponse)
def get_task_notes(
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
def update_task_notes(
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


@router.post("/{task_id}/notes/append", response_model=NotesResponse)
def append_task_note(
    task_id: int,
    request: AppendNotesRequest,
    controller: NotesControllerDep,
    broadcaster: EventBroadcasterDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> NotesResponse:
    """Append content to task notes atomically.

    Unlike ``PUT``, the concatenation happens server-side in a single
    transaction, so concurrent appends never overwrite each other.

    Args:
        task_id: Task ID
        request: Content to append
        controller: Notes controller dependency
        broadcaster: Event broadcaster dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name (used for broadcast exclusion)

    Returns:
        Full notes content after the append and metadata

    Raises:
        HTTPException: 404 if task not found, 422 if the notes would exceed
            ``MAX_NOTES_LENGTH`` after the append
    """
    result = controller.append_notes(
        task_id, request.content, max_length=MAX_NOTES_LENGTH
    )

    # Broadcast WebSocket event in background (exclude the requester by client name)
    broadcaster.task_notes_updated(task_id, result.task_name, client_name)

    # Audit log
    audit_controller.log_operation(
        operation="append_notes",
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
def delete_task_notes(
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
