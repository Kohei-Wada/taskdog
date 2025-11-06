"""Task relationship endpoints (dependencies, tags, hours logging)."""

from datetime import date

from fastapi import APIRouter, HTTPException, status

from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from presentation.api.dependencies import RelationshipControllerDep
from presentation.api.models.requests import (
    AddDependencyRequest,
    LogHoursRequest,
    SetTaskTagsRequest,
)
from presentation.api.models.responses import TaskOperationResponse

router = APIRouter()


def convert_to_task_operation_response(dto) -> TaskOperationResponse:
    """Convert TaskOperationOutput DTO to Pydantic response model."""
    return TaskOperationResponse(
        id=dto.id,
        name=dto.name,
        status=dto.status,
        priority=dto.priority,
        deadline=dto.deadline,
        estimated_duration=dto.estimated_duration,
        planned_start=dto.planned_start,
        planned_end=dto.planned_end,
        actual_start=dto.actual_start,
        actual_end=dto.actual_end,
        depends_on=dto.depends_on,
        tags=dto.tags,
        is_fixed=dto.is_fixed,
        is_archived=dto.is_archived,
        actual_duration_hours=dto.actual_duration_hours,
        actual_daily_hours=dto.actual_daily_hours,
    )


@router.post("/{task_id}/dependencies", response_model=TaskOperationResponse)
async def add_dependency(
    task_id: int, request: AddDependencyRequest, controller: RelationshipControllerDep
):
    """Add a dependency to a task.

    Args:
        task_id: Task ID that will depend on another task
        request: Dependency data (ID of task to depend on)
        controller: Relationship controller dependency

    Returns:
        Updated task data with new dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails (e.g., circular dependency)
    """
    try:
        result = controller.add_dependency(task_id, request.depends_on_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{task_id}/dependencies/{depends_on_id}", response_model=TaskOperationResponse)
async def remove_dependency(
    task_id: int, depends_on_id: int, controller: RelationshipControllerDep
):
    """Remove a dependency from a task.

    Args:
        task_id: Task ID
        depends_on_id: ID of dependency to remove
        controller: Relationship controller dependency

    Returns:
        Updated task data without the dependency

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.remove_dependency(task_id, depends_on_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.put("/{task_id}/tags", response_model=TaskOperationResponse)
async def set_task_tags(
    task_id: int, request: SetTaskTagsRequest, controller: RelationshipControllerDep
):
    """Set task tags (replaces existing tags).

    Args:
        task_id: Task ID
        request: New tags list
        controller: Relationship controller dependency

    Returns:
        Updated task data with new tags

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        result = controller.set_task_tags(task_id, request.tags)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{task_id}/log-hours", response_model=TaskOperationResponse)
async def log_hours(task_id: int, request: LogHoursRequest, controller: RelationshipControllerDep):
    """Log actual hours worked on a task for a specific date.

    Args:
        task_id: Task ID
        request: Hours and date data
        controller: Relationship controller dependency

    Returns:
        Updated task data with logged hours

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
        log_date = request.date if request.date else date.today()
        result = controller.log_hours(task_id, request.hours, log_date.isoformat())
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
