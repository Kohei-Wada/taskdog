"""Task lifecycle endpoints (status changes with time tracking)."""

from fastapi import APIRouter, HTTPException, status

from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
    TaskValidationError,
)
from taskdog_server.api.converters import convert_to_task_operation_response
from taskdog_server.api.dependencies import LifecycleControllerDep
from taskdog_server.api.models.responses import TaskOperationResponse

router = APIRouter()


@router.post("/{task_id}/start", response_model=TaskOperationResponse)
async def start_task(task_id: int, controller: LifecycleControllerDep):
    """Start a task (change status to IN_PROGRESS and record start time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency

    Returns:
        Updated task data with actual_start timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.start_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/complete", response_model=TaskOperationResponse)
async def complete_task(task_id: int, controller: LifecycleControllerDep):
    """Complete a task (change status to COMPLETED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.complete_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/pause", response_model=TaskOperationResponse)
async def pause_task(task_id: int, controller: LifecycleControllerDep):
    """Pause a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.pause_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskNotStartedError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/cancel", response_model=TaskOperationResponse)
async def cancel_task(task_id: int, controller: LifecycleControllerDep):
    """Cancel a task (change status to CANCELED and record end time).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency

    Returns:
        Updated task data with actual_end timestamp

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.cancel_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/reopen", response_model=TaskOperationResponse)
async def reopen_task(task_id: int, controller: LifecycleControllerDep):
    """Reopen a task (change status to PENDING and clear timestamps).

    Args:
        task_id: Task ID
        controller: Lifecycle controller dependency

    Returns:
        Updated task data with cleared timestamps

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.reopen_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
