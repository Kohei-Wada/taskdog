"""Task lifecycle endpoints (status changes with time tracking)."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header

from taskdog_server.api.converters import convert_to_task_operation_response
from taskdog_server.api.dependencies import ConnectionManagerDep, LifecycleControllerDep
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.responses import TaskOperationResponse
from taskdog_server.websocket.broadcaster import broadcast_task_status_changed

router = APIRouter()


@router.post("/{task_id}/start", response_model=TaskOperationResponse)
@handle_task_errors
async def start_task(
    task_id: int,
    controller: LifecycleControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Start a task (change status to IN_PROGRESS and record start time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data with actual_start timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.start_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    background_tasks.add_task(
        broadcast_task_status_changed, manager, result, "PENDING", x_client_id
    )

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/complete", response_model=TaskOperationResponse)
@handle_task_errors
async def complete_task(
    task_id: int,
    controller: LifecycleControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Complete a task (change status to COMPLETED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.complete_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    background_tasks.add_task(
        broadcast_task_status_changed, manager, result, "IN_PROGRESS", x_client_id
    )

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/pause", response_model=TaskOperationResponse)
@handle_task_errors
async def pause_task(
    task_id: int,
    controller: LifecycleControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Pause a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.pause_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    background_tasks.add_task(
        broadcast_task_status_changed, manager, result, "IN_PROGRESS", x_client_id
    )

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/cancel", response_model=TaskOperationResponse)
@handle_task_errors
async def cancel_task(
    task_id: int,
    controller: LifecycleControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Cancel a task (change status to CANCELED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.cancel_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    background_tasks.add_task(
        broadcast_task_status_changed, manager, result, "IN_PROGRESS", x_client_id
    )

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/reopen", response_model=TaskOperationResponse)
@handle_task_errors
async def reopen_task(
    task_id: int,
    controller: LifecycleControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Reopen a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.reopen_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    background_tasks.add_task(
        broadcast_task_status_changed, manager, result, "COMPLETED", x_client_id
    )

    return convert_to_task_operation_response(result)
