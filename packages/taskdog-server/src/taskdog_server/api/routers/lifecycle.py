"""Task lifecycle endpoints (status changes with time tracking)."""

from typing import Annotated

from fastapi import APIRouter, Header

from taskdog_server.api.converters import convert_to_task_operation_response
from taskdog_server.api.dependencies import EventBroadcasterDep, LifecycleControllerDep
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@router.post("/{task_id}/start", response_model=TaskOperationResponse)
@handle_task_errors
async def start_task(
    task_id: int,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    x_client_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Start a task (change status to IN_PROGRESS and record start time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with actual_start timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.start_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcaster.task_status_changed(result, "PENDING", x_client_id, x_user_name)

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/complete", response_model=TaskOperationResponse)
@handle_task_errors
async def complete_task(
    task_id: int,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    x_client_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Complete a task (change status to COMPLETED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.complete_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcaster.task_status_changed(result, "IN_PROGRESS", x_client_id, x_user_name)

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/pause", response_model=TaskOperationResponse)
@handle_task_errors
async def pause_task(
    task_id: int,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    x_client_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Pause a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.pause_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcaster.task_status_changed(result, "IN_PROGRESS", x_client_id, x_user_name)

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/cancel", response_model=TaskOperationResponse)
@handle_task_errors
async def cancel_task(
    task_id: int,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    x_client_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Cancel a task (change status to CANCELED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.cancel_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcaster.task_status_changed(result, "IN_PROGRESS", x_client_id, x_user_name)

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/reopen", response_model=TaskOperationResponse)
@handle_task_errors
async def reopen_task(
    task_id: int,
    controller: LifecycleControllerDep,
    broadcaster: EventBroadcasterDep,
    x_client_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Reopen a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        broadcaster: Event broadcaster dependency
        x_client_id: Optional client ID from WebSocket connection
        x_user_name: Optional user name from API gateway

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.reopen_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcaster.task_status_changed(result, "COMPLETED", x_client_id, x_user_name)

    return convert_to_task_operation_response(result)
