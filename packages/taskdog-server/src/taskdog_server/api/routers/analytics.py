"""Analytics endpoints (statistics, optimization, gantt chart)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status

from taskdog_core.application.dto.query_inputs import GetGanttDataInput
from taskdog_core.domain.exceptions.task_exceptions import (
    NoSchedulableTasksError,
    TaskNotFoundException,
    TaskValidationError,
)
from taskdog_server.api.converters import convert_to_gantt_response
from taskdog_server.api.dependencies import (
    AnalyticsControllerDep,
    BroadcastHelperDep,
    HolidayCheckerDep,
    QueryControllerDep,
)
from taskdog_server.api.models.requests import OptimizeScheduleRequest
from taskdog_server.api.models.responses import (
    CompletionStatistics,
    DeadlineStatistics,
    EstimationStatistics,
    GanttResponse,
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
from taskdog_server.api.utils import parse_iso_date

router = APIRouter()


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    controller: AnalyticsControllerDep,
    period: str = Query("all", description="Time period: all, 7d, or 30d"),
) -> StatisticsResponse:
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
async def get_tag_statistics(controller: QueryControllerDep) -> TagStatisticsResponse:
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
) -> GanttResponse:
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
    # Parse date strings to date objects
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)

    # Create Input DTO (filter building is done in Use Case)
    input_dto = GetGanttDataInput(
        include_archived=all,
        status=status_filter,
        tags=tags or [],
        start_date=start,
        end_date=end,
        sort_by=sort,
        reverse=reverse,
        chart_start_date=start,
        chart_end_date=end,
    )

    # Query gantt data using Use Case pattern
    result = controller.get_gantt_data(
        input_dto=input_dto,
        holiday_checker=holiday_checker,
    )

    # Convert DTO to response model using shared converter
    return convert_to_gantt_response(result)


def run_optimization(
    controller: AnalyticsControllerDep,
    algorithm: str | None,
    start_date: datetime,
    max_hours_per_day: float | None,
    force_override: bool,
    task_ids: list[int] | None = None,
) -> None:
    """Background task to run schedule optimization.

    Args:
        controller: Analytics controller
        algorithm: Algorithm name (None = controller applies default)
        start_date: Optimization start date
        max_hours_per_day: Maximum hours per day (None = controller applies default)
        force_override: Force override existing schedules
        task_ids: Specific task IDs to optimize
    """
    # This runs in the background
    controller.optimize_schedule(
        algorithm=algorithm or "greedy",  # Provide default if None
        start_date=start_date,
        max_hours_per_day=max_hours_per_day,
        force_override=force_override,
        task_ids=task_ids,
    )


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_schedule(
    request: OptimizeScheduleRequest,
    controller: AnalyticsControllerDep,
    broadcast: BroadcastHelperDep,
    run_async: bool = Query(False, description="Run optimization in background"),
    x_client_id: Annotated[str | None, Header()] = None,
) -> OptimizationResponse:
    """Optimize task schedules using specified algorithm.

    Args:
        request: Optimization parameters
        controller: Analytics controller dependency
        broadcast: Broadcast helper dependency
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

        if run_async:
            # Add optimization to background tasks
            broadcast.add_background_task(
                run_optimization,
                controller,
                request.algorithm,
                start_date,
                request.max_hours_per_day,
                request.force_override,
                request.task_ids,
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
            max_hours_per_day=request.max_hours_per_day,
            force_override=request.force_override,
            task_ids=request.task_ids,
        )

        # Broadcast WebSocket event in background (exclude the requester)
        broadcast.schedule_optimized(
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
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except NoSchedulableTasksError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/algorithms", response_model=list[dict[str, str]])
async def list_algorithms(controller: QueryControllerDep) -> list[dict[str, str]]:
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
