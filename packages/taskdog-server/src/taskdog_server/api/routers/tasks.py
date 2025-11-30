"""CRUD endpoints for task management."""

from typing import Annotated

from fastapi import APIRouter, Header, Query, status

from taskdog_core.application.dto.query_inputs import ListTasksInput, TimeRange
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_server.api.converters import (
    convert_to_task_detail_response,
    convert_to_task_list_response,
    convert_to_task_operation_response,
    convert_to_update_task_response,
)
from taskdog_server.api.dependencies import (
    BroadcastHelperDep,
    CrudControllerDep,
    HolidayCheckerDep,
    NotesRepositoryDep,
    QueryControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.requests import CreateTaskRequest, UpdateTaskRequest
from taskdog_server.api.models.responses import (
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    UpdateTaskResponse,
)
from taskdog_server.api.utils import parse_iso_date

router = APIRouter()


@router.post(
    "", response_model=TaskOperationResponse, status_code=status.HTTP_201_CREATED
)
@handle_task_errors
async def create_task(
    request: CreateTaskRequest,
    controller: CrudControllerDep,
    broadcast: BroadcastHelperDep,
    x_client_id: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Create a new task.

    Args:
        request: Task creation data
        controller: CRUD controller dependency
        broadcast: Broadcast helper dependency
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Created task data

    Raises:
        HTTPException: 400 if validation fails
    """
    result = controller.create_task(
        name=request.name,
        priority=request.priority,
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        deadline=request.deadline,
        estimated_duration=request.estimated_duration,
        is_fixed=request.is_fixed,
        tags=request.tags,
    )

    # Broadcast WebSocket event in background (exclude the requester)
    broadcast.task_created(result, x_client_id)

    return convert_to_task_operation_response(result)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    controller: QueryControllerDep,
    notes_repo: NotesRepositoryDep,
    holiday_checker: HolidayCheckerDep,
    all: Annotated[bool, Query(description="Include archived tasks")] = False,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    tags: Annotated[
        list[str] | None, Query(description="Filter by tags (OR logic)")
    ] = None,
    start_date: Annotated[str | None, Query(description="Filter by start date")] = None,
    end_date: Annotated[str | None, Query(description="Filter by end date")] = None,
    sort: Annotated[str, Query(description="Sort field")] = "id",
    reverse: Annotated[bool, Query(description="Reverse sort order")] = False,
    include_gantt: Annotated[
        bool, Query(description="Include Gantt chart data in response")
    ] = False,
    gantt_start_date: Annotated[
        str | None, Query(description="Gantt chart start date (ISO format)")
    ] = None,
    gantt_end_date: Annotated[
        str | None, Query(description="Gantt chart end date (ISO format)")
    ] = None,
) -> TaskListResponse:
    """List tasks with optional filtering and sorting.

    Args:
        controller: Query controller dependency
        holiday_checker: Holiday checker dependency
        all: Include archived tasks
        status_filter: Filter by task status
        tags: Filter by tags (OR logic)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        sort: Sort field name
        reverse: Reverse sort order
        include_gantt: Include Gantt chart data
        gantt_start_date: Gantt chart start date (ISO format)
        gantt_end_date: Gantt chart end date (ISO format)

    Returns:
        List of tasks with metadata, optionally including Gantt data
    """
    # Parse date strings to date objects
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    gantt_start = parse_iso_date(gantt_start_date)
    gantt_end = parse_iso_date(gantt_end_date)

    # Create Input DTO (filter building is done in Use Case)
    input_dto = ListTasksInput(
        include_archived=all,
        status=status_filter,
        tags=tags or [],
        start_date=start,
        end_date=end,
        sort_by=sort,
        reverse=reverse,
    )

    # Query tasks using Use Case pattern
    result = controller.list_tasks(
        input_dto=input_dto,
        include_gantt=include_gantt,
        gantt_start_date=gantt_start,
        gantt_end_date=gantt_end,
        holiday_checker=holiday_checker if include_gantt else None,
    )
    return convert_to_task_list_response(result, notes_repo)


@router.get("/today", response_model=TaskListResponse)
async def list_today_tasks(
    controller: QueryControllerDep,
    notes_repo: NotesRepositoryDep,
    all: Annotated[bool, Query(description="Include archived tasks")] = False,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    sort: Annotated[str, Query(description="Sort field")] = "deadline",
    reverse: Annotated[bool, Query(description="Reverse sort order")] = False,
) -> TaskListResponse:
    """List tasks relevant for today.

    Includes tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS (regardless of dates)

    Args:
        controller: Query controller dependency
        notes_repo: Notes repository dependency
        all: Include archived tasks
        status_filter: Filter by task status
        sort: Sort field name
        reverse: Reverse sort order

    Returns:
        List of tasks relevant for today
    """
    # Create Input DTO with TODAY time range (filter building is done in Use Case)
    input_dto = ListTasksInput(
        include_archived=all,
        status=status_filter,
        time_range=TimeRange.TODAY,
        sort_by=sort,
        reverse=reverse,
    )

    # Query tasks using Use Case pattern
    result = controller.list_tasks(input_dto=input_dto)
    return convert_to_task_list_response(result, notes_repo)


@router.get("/week", response_model=TaskListResponse)
async def list_week_tasks(
    controller: QueryControllerDep,
    notes_repo: NotesRepositoryDep,
    all: Annotated[bool, Query(description="Include archived tasks")] = False,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    sort: Annotated[str, Query(description="Sort field")] = "deadline",
    reverse: Annotated[bool, Query(description="Reverse sort order")] = False,
) -> TaskListResponse:
    """List tasks relevant for this week.

    Includes tasks that meet any of these criteria:
    - Deadline is within this week (Monday to Sunday)
    - Planned period overlaps with this week
    - Status is IN_PROGRESS (regardless of dates)

    Args:
        controller: Query controller dependency
        notes_repo: Notes repository dependency
        all: Include archived tasks
        status_filter: Filter by task status
        sort: Sort field name
        reverse: Reverse sort order

    Returns:
        List of tasks relevant for this week
    """
    # Create Input DTO with THIS_WEEK time range (filter building is done in Use Case)
    input_dto = ListTasksInput(
        include_archived=all,
        status=status_filter,
        time_range=TimeRange.THIS_WEEK,
        sort_by=sort,
        reverse=reverse,
    )

    # Query tasks using Use Case pattern
    result = controller.list_tasks(input_dto=input_dto)
    return convert_to_task_list_response(result, notes_repo)


@router.get("/{task_id}", response_model=TaskDetailResponse)
@handle_task_errors
async def get_task(task_id: int, controller: QueryControllerDep) -> TaskDetailResponse:
    """Get task details by ID.

    Args:
        task_id: Task ID
        controller: Query controller dependency

    Returns:
        Task detail data including notes

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.get_task_detail(task_id)
    return convert_to_task_detail_response(result)


@router.patch("/{task_id}", response_model=UpdateTaskResponse)
@handle_task_errors
async def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    controller: CrudControllerDep,
    broadcast: BroadcastHelperDep,
    x_client_id: Annotated[str | None, Header()] = None,
) -> UpdateTaskResponse:
    """Update task fields.

    Args:
        task_id: Task ID
        request: Fields to update (only provided fields are updated)
        controller: CRUD controller dependency
        broadcast: Broadcast helper dependency
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    result = controller.update_task(
        task_id=task_id,
        name=request.name,
        priority=request.priority,
        status=request.status,
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        deadline=request.deadline,
        estimated_duration=request.estimated_duration,
        is_fixed=request.is_fixed,
        tags=request.tags,
    )

    # Broadcast WebSocket event in background (exclude the requester)
    broadcast.task_updated(result.task, result.updated_fields, x_client_id)

    return convert_to_update_task_response(result)


@router.post("/{task_id}/archive", response_model=TaskOperationResponse)
@handle_task_errors
async def archive_task(
    task_id: int,
    controller: CrudControllerDep,
    broadcast: BroadcastHelperDep,
    x_client_id: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Archive (soft delete) a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        broadcast: Broadcast helper dependency
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Archived task data

    Raises:
        HTTPException: 404 if task not found
    """
    result = controller.archive_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcast.task_updated(result, ["is_archived"], x_client_id)

    return convert_to_task_operation_response(result)


@router.post("/{task_id}/restore", response_model=TaskOperationResponse)
@handle_task_errors
async def restore_task(
    task_id: int,
    controller: CrudControllerDep,
    broadcast: BroadcastHelperDep,
    x_client_id: Annotated[str | None, Header()] = None,
) -> TaskOperationResponse:
    """Restore an archived task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        broadcast: Broadcast helper dependency
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Restored task data

    Raises:
        HTTPException: 404 if task not found, 400 if not archived
    """
    result = controller.restore_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcast.task_updated(result, ["is_archived"], x_client_id)

    return convert_to_task_operation_response(result)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_task_errors
async def delete_task(
    task_id: int,
    controller: CrudControllerDep,
    query_controller: QueryControllerDep,
    broadcast: BroadcastHelperDep,
    x_client_id: Annotated[str | None, Header()] = None,
) -> None:
    """Permanently delete a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        query_controller: Query controller dependency (for fetching task name before deletion)
        broadcast: Broadcast helper dependency
        x_client_id: Optional client ID from WebSocket connection

    Raises:
        HTTPException: 404 if task not found
    """
    # Get task name before deletion for notification
    task_output = query_controller.get_task_by_id(task_id)
    if task_output is None or task_output.task is None:
        raise TaskNotFoundException(f"Task {task_id} not found")
    task_name = task_output.task.name

    # Delete task
    controller.remove_task(task_id)

    # Broadcast WebSocket event in background (exclude the requester)
    broadcast.task_deleted(task_id, task_name, x_client_id)
