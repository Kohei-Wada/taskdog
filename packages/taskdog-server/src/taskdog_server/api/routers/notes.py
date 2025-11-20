"""Task notes endpoints (CRUD operations for markdown notes)."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_server.api.dependencies import (
    ConnectionManagerDep,
    NotesRepositoryDep,
    RepositoryDep,
)
from taskdog_server.api.models.requests import UpdateNotesRequest
from taskdog_server.api.models.responses import NotesResponse
from taskdog_server.websocket.broadcaster import broadcast_task_notes_updated

router = APIRouter()


@router.get("/{task_id}/notes", response_model=NotesResponse)
async def get_task_notes(
    task_id: int, repository: RepositoryDep, notes_repo: NotesRepositoryDep
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
    try:
        # Verify task exists
        task = repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)

        # Get notes
        has_notes = notes_repo.has_notes(task_id)
        content = notes_repo.read_notes(task_id) or ""

        return NotesResponse(task_id=task_id, content=content, has_notes=has_notes)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{task_id}/notes", response_model=NotesResponse)
async def update_task_notes(
    task_id: int,
    request: UpdateNotesRequest,
    repository: RepositoryDep,
    notes_repo: NotesRepositoryDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
) -> NotesResponse:
    """Update task notes.

    Args:
        task_id: Task ID
        request: Notes content
        repository: Task repository dependency
        notes_repo: Notes repository dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated notes content and metadata

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        # Verify task exists
        task = repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)

        # Update notes
        notes_repo.write_notes(task_id, request.content)
        has_notes = notes_repo.has_notes(task_id)

        # Broadcast WebSocket event in background (exclude the requester)
        background_tasks.add_task(
            broadcast_task_notes_updated, manager, task_id, task.name, x_client_id
        )

        return NotesResponse(
            task_id=task_id, content=request.content, has_notes=has_notes
        )
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{task_id}/notes", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_notes(
    task_id: int,
    repository: RepositoryDep,
    notes_repo: NotesRepositoryDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
) -> None:
    """Delete task notes.

    Args:
        task_id: Task ID
        repository: Task repository dependency
        notes_repo: Notes repository dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        # Verify task exists
        task = repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)

        # Delete notes by writing empty content
        notes_repo.write_notes(task_id, "")

        # Broadcast WebSocket event in background (exclude the requester)
        background_tasks.add_task(
            broadcast_task_notes_updated, manager, task_id, task.name, x_client_id
        )
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
