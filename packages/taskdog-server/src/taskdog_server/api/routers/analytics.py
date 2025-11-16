"""Analytics endpoints (statistics, optimization, gantt chart)."""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status

from taskdog_core.application.queries.filters.date_range_filter import DateRangeFilter
from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.application.queries.filters.tag_filter import TagFilter
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_server.api.dependencies import (
    AnalyticsControllerDep,
    ConnectionManagerDep,
    HolidayCheckerDep,
    QueryControllerDep,
)
from taskdog_server.api.models.requests import OptimizeScheduleRequest
from taskdog_server.api.models.responses import (
    CompletionStatistics,
    DeadlineStatistics,
    EstimationStatistics,
    GanttDateRange,
    GanttResponse,
    GanttTaskResponse,
    OptimizationResponse,
    OptimizationSummary,
    PriorityDistribution,
    SchedulingFailure,
    StatisticsResponse,
    TagStatisticsItem,
    TagStatisticsResponse,
    TimeStatistics,
    TrendData,
)
from taskdog_server.websocket.broadcaster import broadcast_schedule_optimized

router = APIRouter()


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    controller: AnalyticsControllerDep,
    period: str = Query("all", description="Time period: all, 7d, or 30d"),
):
    """Get task statistics for a time period.

    Args:
        controller: Analytics controller dependency
        period: Time period (all, 7d, 30d)

    Returns:
        Task statistics including completion, time, estimation, deadline, and trends

    Raises:
        HTTPException: 400 if period is invalid
    """
    if period not in ["all", "7d", "30d"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be one of: all, 7d, 30d",
        )

    try:
        result = controller.calculate_statistics(period=period)

        # Convert DTO to response model
        response = StatisticsResponse(
            completion=CompletionStatistics(
                total=result.task_stats.total_tasks,
                completed=result.task_stats.completed_count,
                in_progress=result.task_stats.in_progress_count,
                pending=result.task_stats.pending_count,
                canceled=result.task_stats.canceled_count,
                completion_rate=result.task_stats.completion_rate,
            ),
            time=(
                TimeStatistics(
                    total_logged_hours=result.time_stats.total_work_hours,
                    average_task_duration=result.time_stats.average_work_hours,
                    total_estimated_hours=0.0,  # Not available in DTO
                )
                if result.time_stats
                else None
            ),
            estimation=(
                EstimationStatistics(
                    average_deviation=0.0,  # Need to calculate from accuracy_rate
                    average_deviation_percentage=result.estimation_stats.accuracy_rate
                    * 100,
                    tasks_with_estimates=result.estimation_stats.total_tasks_with_estimation,
                )
                if result.estimation_stats
                else None
            ),
            deadline=(
                DeadlineStatistics(
                    met=result.deadline_stats.met_deadline_count,
                    missed=result.deadline_stats.missed_deadline_count,
                    no_deadline=0,  # Not available in DTO
                    adherence_rate=result.deadline_stats.compliance_rate,
                )
                if result.deadline_stats
                else None
            ),
            priority=PriorityDistribution(
                distribution=result.priority_stats.priority_completion_map
            ),
            trends=(
                TrendData(
                    completed_per_day={},  # Need to map from weekly/monthly trends
                    hours_per_day={},  # Not available in DTO
                )
                if result.trend_stats
                else None
            ),
        )
        return response
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/tags/statistics", response_model=TagStatisticsResponse)
async def get_tag_statistics(controller: QueryControllerDep):
    """Get tag usage statistics.

    Args:
        controller: Query controller dependency

    Returns:
        Tag statistics including count and completion rate per tag
    """
    result = controller.get_tag_statistics()

    # Convert DTO to response model
    # Note: TagStatisticsOutput.tag_counts is a dict[str, int]
    # completion_rate is not available in the DTO, so we set it to 0.0
    tags = [
        TagStatisticsItem(tag=tag_name, count=count, completion_rate=0.0)
        for tag_name, count in result.tag_counts.items()
    ]

    return TagStatisticsResponse(tags=tags, total_tags=result.total_tags)


@router.get("/gantt", response_model=GanttResponse)
async def get_gantt_chart(
    controller: QueryControllerDep,
    holiday_checker: HolidayCheckerDep,
    all: Annotated[bool, Query(description="Include archived tasks")] = False,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    tags: Annotated[
        list[str] | None, Query(description="Filter by tags (OR logic)")
    ] = None,
    start_date: Annotated[
        str | None, Query(description="Chart start date (ISO format)")
    ] = None,
    end_date: Annotated[
        str | None, Query(description="Chart end date (ISO format)")
    ] = None,
    sort: Annotated[str, Query(description="Sort field")] = "deadline",
    reverse: Annotated[bool, Query(description="Reverse sort order")] = False,
):
    """Get Gantt chart data with workload calculations.

    Args:
        controller: Query controller dependency
        holiday_checker: Holiday checker dependency
        all: Include archived tasks
        status_filter: Filter by task status
        tags: Filter by tags (OR logic)
        start_date: Chart start date
        end_date: Chart end date
        sort: Sort field name
        reverse: Reverse sort order

    Returns:
        Gantt chart data with tasks, daily hours, workload, and holidays
    """
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

    # Parse dates
    start_date_obj = date.fromisoformat(start_date) if start_date else None
    end_date_obj = date.fromisoformat(end_date) if end_date else None

    # Query gantt data
    result = controller.get_gantt_data(
        filter_obj=filter_obj,
        sort_by=sort,
        reverse=reverse,
        start_date=start_date_obj,
        end_date=end_date_obj,
        holiday_checker=holiday_checker,
    )

    # Convert DTO to response model
    tasks = [
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
                for date_obj, hours in result.task_daily_hours.get(task.id, {}).items()
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
        date_obj.isoformat(): hours for date_obj, hours in result.daily_workload.items()
    }

    # Convert holidays (set of dates to list of ISO strings)
    holidays = [holiday.isoformat() for holiday in result.holidays]

    return GanttResponse(
        date_range=GanttDateRange(
            start_date=result.date_range.start_date, end_date=result.date_range.end_date
        ),
        tasks=tasks,
        task_daily_hours=task_daily_hours,
        daily_workload=daily_workload,
        holidays=holidays,
    )


def run_optimization(
    controller,
    algorithm: str,
    start_date: datetime,
    max_hours_per_day: float,
    force_override: bool,
) -> None:
    """Background task to run schedule optimization.

    Args:
        controller: Analytics controller
        algorithm: Algorithm name
        start_date: Optimization start date
        max_hours_per_day: Maximum hours per day
        force_override: Force override existing schedules
    """
    # This runs in the background
    controller.optimize_schedule(
        algorithm=algorithm,
        start_date=start_date,
        max_hours_per_day=max_hours_per_day,
        force_override=force_override,
    )


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_schedule(
    request: OptimizeScheduleRequest,
    controller: AnalyticsControllerDep,
    manager: ConnectionManagerDep,
    background_tasks: BackgroundTasks,
    run_async: bool = Query(False, description="Run optimization in background"),
    x_client_id: Annotated[str | None, Header()] = None,
):
    """Optimize task schedules using specified algorithm.

    Args:
        request: Optimization parameters
        controller: Analytics controller dependency
        background_tasks: FastAPI background tasks
        run_async: If True, run in background and return immediately
        x_client_id: Optional client ID from WebSocket connection

    Returns:
        Optimization results with summary and failures

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Use current date if not specified
        start_date = request.start_date if request.start_date else datetime.now()

        # Use config default if not specified
        max_hours = request.max_hours_per_day if request.max_hours_per_day else 8.0

        if run_async:
            # Add to background tasks
            background_tasks.add_task(
                run_optimization,
                controller,
                request.algorithm,
                start_date,
                max_hours,
                request.force_override,
            )
            return OptimizationResponse(
                summary=OptimizationSummary(
                    total_tasks=0,
                    scheduled_tasks=0,
                    failed_tasks=0,
                    total_hours=0.0,
                    start_date=start_date.date(),
                    end_date=start_date.date(),
                    algorithm=request.algorithm,
                ),
                failures=[],
                message="Optimization started in background. Check task schedules later.",
            )

        # Run synchronously
        result = controller.optimize_schedule(
            algorithm=request.algorithm,
            start_date=start_date,
            max_hours_per_day=max_hours,
            force_override=request.force_override,
        )

        # Broadcast WebSocket event in background (exclude the requester)
        background_tasks.add_task(
            broadcast_schedule_optimized,
            manager,
            len(result.successful_tasks),
            len(result.failed_tasks),
            request.algorithm,
            x_client_id,
        )

        # Convert DTO to response model
        failures = [
            SchedulingFailure(task_id=f.task.id, task_name=f.task.name, reason=f.reason)
            for f in result.failed_tasks
        ]

        # Calculate date range from daily allocations
        if result.daily_allocations:
            dates = list(result.daily_allocations.keys())
            opt_start_date = min(dates)
            opt_end_date = max(dates)
        else:
            opt_start_date = start_date.date()
            opt_end_date = start_date.date()

        # Build optimization message
        if result.all_failed():
            message = (
                f"No tasks were scheduled. {len(result.failed_tasks)} task(s) failed."
            )
        elif result.has_failures():
            message = f"Partially optimized: {len(result.successful_tasks)} succeeded, {len(result.failed_tasks)} failed."
        else:
            message = f"Successfully optimized {len(result.successful_tasks)} task(s)."

        return OptimizationResponse(
            summary=OptimizationSummary(
                total_tasks=len(result.successful_tasks) + len(result.failed_tasks),
                scheduled_tasks=len(result.successful_tasks),
                failed_tasks=len(result.failed_tasks),
                total_hours=result.summary.total_hours,
                start_date=opt_start_date,
                end_date=opt_end_date,
                algorithm=request.algorithm,
            ),
            failures=failures,
            message=message,
        )
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/algorithms", response_model=list[dict[str, str]])
async def list_algorithms(controller: QueryControllerDep):
    """List available optimization algorithms.

    Args:
        controller: Query controller dependency

    Returns:
        List of algorithms with name, display name, and description
    """
    algorithms = controller.get_algorithm_metadata()
    return [
        {"name": name, "display_name": display_name, "description": description}
        for name, display_name, description in algorithms
    ]
