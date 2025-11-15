"""CRUD endpoints for task management."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status

from taskdog_core.application.queries.filters.date_range_filter import DateRangeFilter
from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.application.queries.filters.tag_filter import TagFilter
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskValidationError,
)
from taskdog_server.api.converters import (
    convert_to_task_detail_response,
    convert_to_task_list_response,
    convert_to_task_operation_response,
    convert_to_update_task_response,
)
from taskdog_server.api.dependencies import (
    CrudControllerDep,
    HolidayCheckerDep,
    NotesRepositoryDep,
    QueryControllerDep,
)
from taskdog_server.api.models.requests import CreateTaskRequest, UpdateTaskRequest
from taskdog_server.api.models.responses import (
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    UpdateTaskResponse,
)
from taskdog_server.api.routers.websocket import get_connection_manager
from taskdog_server.websocket.broadcaster import (
    broadcast_task_created,
    broadcast_task_deleted,
    broadcast_task_updated,
)

router = APIRouter()


@router.post(
    "", response_model=TaskOperationResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    request: CreateTaskRequest,
    controller: CrudControllerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Create a new task.

    Args:
        request: Task creation data
        controller: CRUD controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Created task data

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
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
        manager = get_connection_manager()
        background_tasks.add_task(broadcast_task_created, manager, result, x_client_id)

        return convert_to_task_operation_response(result)
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


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
):
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
    from datetime import datetime

    # Build filter using >> operator to compose filters
    filter_obj: TaskFilter | None = None

    # Archive filter (unless --all is specified)
    if not all:
        filter_obj = NonArchivedFilter()

    # Status filter
    if status_filter:
        from taskdog_core.domain.entities.task import TaskStatus

        status_f = StatusFilter(status=TaskStatus[status_filter.upper()])
        filter_obj = filter_obj >> status_f if filter_obj else status_f

    # Tag filter
    if tags:
        tag_f = TagFilter(tags=tags, match_all=False)
        filter_obj = filter_obj >> tag_f if filter_obj else tag_f

    # Date range filter
    if start_date or end_date:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        date_f = DateRangeFilter(start_date=start, end_date=end)
        filter_obj = filter_obj >> date_f if filter_obj else date_f

    # Parse Gantt date range
    gantt_start = (
        datetime.fromisoformat(gantt_start_date).date() if gantt_start_date else None
    )
    gantt_end = (
        datetime.fromisoformat(gantt_end_date).date() if gantt_end_date else None
    )

    # Query tasks with optional Gantt data
    result = controller.list_tasks(
        filter_obj=filter_obj,
        sort_by=sort,
        reverse=reverse,
        include_gantt=include_gantt,
        gantt_start_date=gantt_start,
        gantt_end_date=gantt_end,
        holiday_checker=holiday_checker if include_gantt else None,
    )
    return convert_to_task_list_response(result, notes_repo)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: int, controller: QueryControllerDep):
    """Get task details by ID.

    Args:
        task_id: Task ID
        controller: Query controller dependency

    Returns:
        Task detail data including notes

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        result = controller.get_task_detail(task_id)
        return convert_to_task_detail_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{task_id}", response_model=UpdateTaskResponse)
async def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    controller: CrudControllerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Update task fields.

    Args:
        task_id: Task ID
        request: Fields to update (only provided fields are updated)
        controller: CRUD controller dependency
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Updated task data

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    try:
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
        manager = get_connection_manager()
        background_tasks.add_task(
            broadcast_task_updated,
            manager,
            result.task,
            result.updated_fields,
            x_client_id,
        )

        return convert_to_update_task_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/archive", response_model=TaskOperationResponse)
async def archive_task(
    task_id: int, controller: CrudControllerDep, background_tasks: BackgroundTasks
):
    """Archive (soft delete) a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        background_tasks: Background tasks for WebSocket notifications

    Returns:
        Archived task data

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        result = controller.archive_task(task_id)

        # Broadcast WebSocket event in background
        manager = get_connection_manager()
        background_tasks.add_task(
            broadcast_task_updated, manager, result, ["is_archived"]
        )

        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{task_id}/restore", response_model=TaskOperationResponse)
async def restore_task(
    task_id: int, controller: CrudControllerDep, background_tasks: BackgroundTasks
):
    """Restore an archived task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        background_tasks: Background tasks for WebSocket notifications

    Returns:
        Restored task data

    Raises:
        HTTPException: 404 if task not found, 400 if not archived
    """
    try:
        result = controller.restore_task(task_id)

        # Broadcast WebSocket event in background
        manager = get_connection_manager()
        background_tasks.add_task(
            broadcast_task_updated, manager, result, ["is_archived"]
        )

        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    controller: CrudControllerDep,
    query_controller: QueryControllerDep,
    background_tasks: BackgroundTasks,
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Permanently delete a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency
        query_controller: Query controller dependency (for fetching task name before deletion)
        background_tasks: Background tasks for WebSocket notifications
        x_client_id: Optional client ID from WebSocket connection

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        # Get task name before deletion for notification
        task_output = query_controller.get_task_by_id(task_id)
        if task_output is None or task_output.task is None:
            raise TaskNotFoundException(f"Task {task_id} not found")
        task_name = task_output.task.name

        # Delete task
        controller.remove_task(task_id)

        # Broadcast WebSocket event in background (exclude the requester)
        manager = get_connection_manager()
        background_tasks.add_task(
            broadcast_task_deleted, manager, task_id, task_name, x_client_id
        )

    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
