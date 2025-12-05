"""Task notes endpoints (CRUD operations for markdown notes)."""

from fastapi import APIRouter, status

from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_server.api.dependencies import (
    AuditLoggerDep,
    AuthenticatedClientDep,
    EventBroadcasterDep,
    NotesRepositoryDep,
    RepositoryDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import UpdateNotesRequest
from taskdog_server.api.models.responses import NotesResponse

router = APIRouter()


@router.get("/{task_id}/notes", response_model=NotesResponse)
@handle_task_errors
async def get_task_notes(
    task_id: int,
    repository: RepositoryDep,
    notes_repo: NotesRepositoryDep,
    _client_name: AuthenticatedClientDep,
) -> NotesResponse:
    """Get task notes.

    Args:
        task_id: Task ID
        repository: Task repository dependency
        notes_repo: Notes repository dependency

    Returns:
        Notes content and metadata

    Raises:
        HTTPException: 404 if task not found
    """
    # Verify task exists
    task = repository.get_by_id(task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    # Get notes
    has_notes = notes_repo.has_notes(task_id)
    content = notes_repo.read_notes(task_id) or ""

    return NotesResponse(task_id=task_id, content=content, has_notes=has_notes)


@router.put("/{task_id}/notes", response_model=NotesResponse)
@handle_task_errors
async def update_task_notes(
    task_id: int,
    request: UpdateNotesRequest,
    repository: RepositoryDep,
    notes_repo: NotesRepositoryDep,
    broadcaster: EventBroadcasterDep,
    audit_logger: AuditLoggerDep,
    client_name: AuthenticatedClientDep,
) -> NotesResponse:
    """Update task notes.

    Args:
        task_id: Task ID
        request: Notes content
        repository: Task repository dependency
        notes_repo: Notes repository dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (used for broadcast exclusion)

    Returns:
        Updated notes content and metadata

    Raises:
        HTTPException: 404 if task not found
    """
    # Verify task exists
    task = repository.get_by_id(task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    # Update notes
    notes_repo.write_notes(task_id, request.content)
    has_notes = notes_repo.has_notes(task_id)

    # Broadcast WebSocket event in background (exclude the requester by client name)
    broadcaster.task_notes_updated(task_id, task.name, client_name)

    # Audit log
    audit_logger.log_operation(
        operation="update_notes",
        resource_type="task",
        resource_id=task_id,
        resource_name=task.name,
        client_name=client_name,
        new_values={"has_notes": has_notes},
        success=True,
    )

    return NotesResponse(task_id=task_id, content=request.content, has_notes=has_notes)


@router.delete("/{task_id}/notes", status_code=status.HTTP_204_NO_CONTENT)
@handle_task_errors
async def delete_task_notes(
    task_id: int,
    repository: RepositoryDep,
    notes_repo: NotesRepositoryDep,
    broadcaster: EventBroadcasterDep,
    audit_logger: AuditLoggerDep,
    client_name: AuthenticatedClientDep,
) -> None:
    """Delete task notes.

    Args:
        task_id: Task ID
        repository: Task repository dependency
        notes_repo: Notes repository dependency
        broadcaster: Event broadcaster dependency
        client_name: Authenticated client name (used for broadcast exclusion)

    Raises:
        HTTPException: 404 if task not found
    """
    # Verify task exists
    task = repository.get_by_id(task_id)
    if task is None:
        raise TaskNotFoundException(task_id)

    # Delete notes by writing empty content
    notes_repo.write_notes(task_id, "")

    # Broadcast WebSocket event in background (exclude the requester by client name)
    broadcaster.task_notes_updated(task_id, task.name, client_name)

    # Audit log
    audit_logger.log_operation(
        operation="delete_notes",
        resource_type="task",
        resource_id=task_id,
        resource_name=task.name,
        client_name=client_name,
        success=True,
    )
