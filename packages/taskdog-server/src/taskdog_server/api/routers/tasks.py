"""CRUD endpoints for task management."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

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
    TaskResponse,
    UpdateTaskResponse,
)

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


def convert_to_update_task_response(dto) -> UpdateTaskResponse:
    """Convert UpdateTaskOutput DTO to Pydantic response model."""
    task = dto.task  # UpdateTaskOutput has nested task attribute
    return UpdateTaskResponse(
        id=task.id,
        name=task.name,
        status=task.status,
        priority=task.priority,
        deadline=task.deadline,
        estimated_duration=task.estimated_duration,
        planned_start=task.planned_start,
        planned_end=task.planned_end,
        actual_start=task.actual_start,
        actual_end=task.actual_end,
        depends_on=task.depends_on,
        tags=task.tags,
        is_fixed=task.is_fixed,
        is_archived=task.is_archived,
        actual_duration_hours=task.actual_duration_hours,
        actual_daily_hours=task.actual_daily_hours,
        updated_fields=dto.updated_fields,
    )


def convert_to_task_list_response(dto, notes_repo) -> TaskListResponse:
    """Convert TaskListOutput DTO to Pydantic response model.

    Args:
        dto: TaskListOutput DTO from controller
        notes_repo: Notes repository for checking note existence

    Returns:
        TaskListResponse with has_notes field populated
    """
    from taskdog_server.api.models.responses import (
        GanttDateRange,
        GanttResponse,
        GanttTaskResponse,
    )

    tasks = [
        TaskResponse(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            estimated_duration=task.estimated_duration,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            actual_duration_hours=task.actual_duration_hours,
            depends_on=task.depends_on,
            tags=task.tags,
            is_fixed=task.is_fixed,
            is_archived=task.is_archived,
            is_finished=task.is_finished,
            has_notes=notes_repo.has_notes(task.id),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in dto.tasks
    ]

    # Convert gantt_data if present
    gantt = None
    if dto.gantt_data:
        result = dto.gantt_data
        gantt_tasks = [
            GanttTaskResponse(
                id=task.id,
                name=task.name,
                status=task.status,
                estimated_duration=task.estimated_duration,
                planned_start=task.planned_start,
                planned_end=task.planned_end,
                actual_start=task.actual_start,
                actual_end=task.actual_end,
                deadline=task.deadline,
                is_fixed=False,  # Not available in GanttTaskDto
                is_archived=False,  # Not available in GanttTaskDto
                daily_allocations={
                    date_obj.isoformat(): hours
                    for date_obj, hours in result.task_daily_hours.get(
                        task.id, {}
                    ).items()
                },
            )
            for task in result.tasks
        ]

        # Convert task_daily_hours (nested dict with date keys)
        task_daily_hours = {
            task_id: {
                date_obj.isoformat(): hours for date_obj, hours in daily_hours.items()
            }
            for task_id, daily_hours in result.task_daily_hours.items()
        }

        # Convert daily_workload
        daily_workload = {
            date_obj.isoformat(): hours
            for date_obj, hours in result.daily_workload.items()
        }

        # Convert holidays (set of dates to list of ISO strings)
        holidays = [holiday.isoformat() for holiday in result.holidays]

        gantt = GanttResponse(
            date_range=GanttDateRange(
                start_date=result.date_range.start_date,
                end_date=result.date_range.end_date,
            ),
            tasks=gantt_tasks,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
            holidays=holidays,
        )

    return TaskListResponse(
        tasks=tasks,
        total_count=dto.total_count,
        filtered_count=dto.filtered_count,
        gantt=gantt,
    )


def convert_to_task_detail_response(dto) -> TaskDetailResponse:
    """Convert GetTaskDetailOutput DTO to Pydantic response model."""
    return TaskDetailResponse(
        id=dto.task.id,
        name=dto.task.name,
        priority=dto.task.priority,
        status=dto.task.status,
        planned_start=dto.task.planned_start,
        planned_end=dto.task.planned_end,
        deadline=dto.task.deadline,
        estimated_duration=dto.task.estimated_duration,
        actual_start=dto.task.actual_start,
        actual_end=dto.task.actual_end,
        depends_on=dto.task.depends_on,
        tags=dto.task.tags,
        is_fixed=dto.task.is_fixed,
        is_archived=dto.task.is_archived,
        daily_allocations={
            date.isoformat(): hours
            for date, hours in dto.task.daily_allocations.items()
        },
        actual_daily_hours={
            date.isoformat(): hours
            for date, hours in dto.task.actual_daily_hours.items()
        },
        actual_duration_hours=dto.task.actual_duration_hours,
        is_active=dto.task.is_active,
        is_finished=dto.task.is_finished,
        can_be_modified=dto.task.can_be_modified,
        is_schedulable=dto.task.is_schedulable,
        notes=dto.notes_content,
        created_at=dto.task.created_at,
        updated_at=dto.task.updated_at,
    )


@router.post(
    "", response_model=TaskOperationResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(request: CreateTaskRequest, controller: CrudControllerDep):
    """Create a new task.

    Args:
        request: Task creation data
        controller: CRUD controller dependency

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
    task_id: int, request: UpdateTaskRequest, controller: CrudControllerDep
):
    """Update task fields.

    Args:
        task_id: Task ID
        request: Fields to update (only provided fields are updated)
        controller: CRUD controller dependency

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
        return convert_to_update_task_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (TaskValidationError, TaskAlreadyFinishedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{task_id}/archive", response_model=TaskOperationResponse)
async def archive_task(task_id: int, controller: CrudControllerDep):
    """Archive (soft delete) a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency

    Returns:
        Archived task data

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        result = controller.archive_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{task_id}/restore", response_model=TaskOperationResponse)
async def restore_task(task_id: int, controller: CrudControllerDep):
    """Restore an archived task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency

    Returns:
        Restored task data

    Raises:
        HTTPException: 404 if task not found, 400 if not archived
    """
    try:
        result = controller.restore_task(task_id)
        return convert_to_task_operation_response(result)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, controller: CrudControllerDep):
    """Permanently delete a task.

    Args:
        task_id: Task ID
        controller: CRUD controller dependency

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        controller.remove_task(task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
