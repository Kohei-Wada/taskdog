"""DTO converters for API responses.

Converts JSON responses from API to taskdog-core DTOs.
Single source of truth for all API-to-DTO transformations.
"""

from datetime import date as date_type
from datetime import datetime
from typing import Any

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
from taskdog_core.application.dto.optimization_output import (
    OptimizationOutput,
    SchedulingFailure,
)
from taskdog_core.application.dto.optimization_summary import OptimizationSummary
from taskdog_core.application.dto.simulation_result import SimulationResult
from taskdog_core.application.dto.statistics_output import (
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import (
    GanttTaskDto,
    TaskDetailDto,
    TaskRowDto,
    TaskSummaryDto,
)
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import TaskStatus

# === Datetime Conversion Utilities ===


def _parse_optional_datetime(data: dict[str, Any], field: str) -> datetime | None:
    """Parse ISO datetime from dict, returning None if field missing/None.

    Args:
        data: Dictionary containing datetime fields
        field: Field name to extract

    Returns:
        Parsed datetime or None if field is missing/None
    """
    value = data.get(field)
    return datetime.fromisoformat(value) if value else None


def _parse_optional_date(data: dict[str, Any], field: str) -> date_type | None:
    """Parse ISO date from dict, returning None if field missing/None.

    Args:
        data: Dictionary containing date fields
        field: Field name to extract

    Returns:
        Parsed date or None if field is missing/None
    """
    value = data.get(field)
    return date_type.fromisoformat(value) if value else None


def _parse_datetime_fields(
    data: dict[str, Any], fields: list[str]
) -> dict[str, datetime | None]:
    """Parse multiple datetime fields from API response.

    Args:
        data: Dictionary containing datetime fields
        fields: List of field names to parse

    Returns:
        Dictionary mapping field names to parsed datetime values
    """
    return {field: _parse_optional_datetime(data, field) for field in fields}


def convert_to_task_operation_output(data: dict[str, Any]) -> TaskOperationOutput:
    """Convert API response to TaskOperationOutput.

    Args:
        data: API response data

    Returns:
        TaskOperationOutput with task data
    """
    # Parse datetime fields using utility
    dt_fields = _parse_datetime_fields(
        data, ["deadline", "planned_start", "planned_end", "actual_start", "actual_end"]
    )

    return TaskOperationOutput(
        id=data["id"],
        name=data["name"],
        status=TaskStatus(data["status"]),
        priority=data["priority"],
        deadline=dt_fields["deadline"],
        estimated_duration=data.get("estimated_duration"),
        planned_start=dt_fields["planned_start"],
        planned_end=dt_fields["planned_end"],
        actual_start=dt_fields["actual_start"],
        actual_end=dt_fields["actual_end"],
        depends_on=data.get("depends_on", []),
        tags=data.get("tags", []),
        is_fixed=data.get("is_fixed", False),
        is_archived=data.get("is_archived", False),
        actual_duration_hours=data.get("actual_duration_hours"),
        actual_daily_hours=data.get("actual_daily_hours", {}),
    )


def convert_to_update_task_output(data: dict[str, Any]) -> TaskUpdateOutput:
    """Convert API response to TaskUpdateOutput.

    Args:
        data: API response data

    Returns:
        TaskUpdateOutput with updated task data and fields
    """
    # Reuse convert_to_task_operation_output to avoid duplication
    task = convert_to_task_operation_output(data)

    # Construct TaskUpdateOutput with nested task and updated_fields
    return TaskUpdateOutput(
        task=task,
        updated_fields=data.get("updated_fields", []),
    )


def convert_to_task_list_output(
    data: dict[str, Any], has_notes_cache: dict[int, bool] | None = None
) -> TaskListOutput:
    """Convert API response to TaskListOutput.

    Args:
        data: API response data
        has_notes_cache: Optional cache dictionary to populate with has_notes info

    Returns:
        TaskListOutput with task list and metadata
    """
    tasks = []
    for task in data["tasks"]:
        # Cache has_notes information if cache provided
        if has_notes_cache is not None:
            has_notes_cache[task["id"]] = task.get("has_notes", False)

        # Parse datetime fields using utility
        dt_fields = _parse_datetime_fields(
            task,
            ["planned_start", "planned_end", "deadline", "actual_start", "actual_end"],
        )

        tasks.append(
            TaskRowDto(
                id=task["id"],
                name=task["name"],
                priority=task["priority"],
                status=TaskStatus(task["status"]),
                planned_start=dt_fields["planned_start"],
                planned_end=dt_fields["planned_end"],
                deadline=dt_fields["deadline"],
                actual_start=dt_fields["actual_start"],
                actual_end=dt_fields["actual_end"],
                estimated_duration=task.get("estimated_duration"),
                actual_duration_hours=task.get("actual_duration_hours"),
                is_fixed=task.get("is_fixed", False),
                depends_on=task.get("depends_on", []),
                tags=task.get("tags", []),
                is_archived=task.get("is_archived", False),
                is_finished=task.get("is_finished", False),
                created_at=datetime.fromisoformat(task["created_at"]),
                updated_at=datetime.fromisoformat(task["updated_at"]),
            )
        )

    # Convert gantt data if present
    gantt_data = None
    if data.get("gantt"):
        gantt_data = convert_to_gantt_output(data["gantt"])

    return TaskListOutput(
        tasks=tasks,
        total_count=data["total_count"],
        filtered_count=data["filtered_count"],
        gantt_data=gantt_data,
    )


def convert_to_get_task_by_id_output(data: dict[str, Any]) -> TaskByIdOutput:
    """Convert API response to TaskByIdOutput.

    Args:
        data: API response data

    Returns:
        TaskByIdOutput with task data
    """
    # Parse datetime fields using utility
    dt_fields = _parse_datetime_fields(
        data, ["planned_start", "planned_end", "deadline", "actual_start", "actual_end"]
    )

    # Convert task data (same as get_task_detail but without notes)
    task = TaskDetailDto(
        id=data["id"],
        name=data["name"],
        priority=data["priority"],
        status=TaskStatus(data["status"]),
        planned_start=dt_fields["planned_start"],
        planned_end=dt_fields["planned_end"],
        deadline=dt_fields["deadline"],
        actual_start=dt_fields["actual_start"],
        actual_end=dt_fields["actual_end"],
        estimated_duration=data.get("estimated_duration"),
        daily_allocations={
            date_type.fromisoformat(k): v
            for k, v in data.get("daily_allocations", {}).items()
        },
        is_fixed=data.get("is_fixed", False),
        depends_on=data.get("depends_on", []),
        actual_daily_hours={
            date_type.fromisoformat(k): v
            for k, v in data.get("actual_daily_hours", {}).items()
        },
        tags=data.get("tags", []),
        is_archived=data.get("is_archived", False),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        actual_duration_hours=data.get("actual_duration_hours"),
        is_active=data.get("is_active", False),
        is_finished=data.get("is_finished", False),
        can_be_modified=data.get("can_be_modified", False),
        is_schedulable=data.get("is_schedulable", False),
    )

    return TaskByIdOutput(task=task)


def convert_to_get_task_detail_output(data: dict[str, Any]) -> TaskDetailOutput:
    """Convert API response to TaskDetailOutput.

    Args:
        data: API response data

    Returns:
        TaskDetailOutput with task data and notes
    """
    # Parse datetime fields using utility
    dt_fields = _parse_datetime_fields(
        data, ["planned_start", "planned_end", "deadline", "actual_start", "actual_end"]
    )

    # Convert task data
    task = TaskDetailDto(
        id=data["id"],
        name=data["name"],
        priority=data["priority"],
        status=TaskStatus(data["status"]),
        planned_start=dt_fields["planned_start"],
        planned_end=dt_fields["planned_end"],
        deadline=dt_fields["deadline"],
        actual_start=dt_fields["actual_start"],
        actual_end=dt_fields["actual_end"],
        estimated_duration=data.get("estimated_duration"),
        daily_allocations={
            date_type.fromisoformat(k): v
            for k, v in data.get("daily_allocations", {}).items()
        },
        is_fixed=data.get("is_fixed", False),
        depends_on=data.get("depends_on", []),
        actual_daily_hours={
            date_type.fromisoformat(k): v
            for k, v in data.get("actual_daily_hours", {}).items()
        },
        tags=data.get("tags", []),
        is_archived=data.get("is_archived", False),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        actual_duration_hours=data.get("actual_duration_hours"),
        is_active=data.get("is_active", False),
        is_finished=data.get("is_finished", False),
        can_be_modified=data.get("can_be_modified", False),
        is_schedulable=data.get("is_schedulable", False),
    )

    # Extract notes
    notes_content = data.get("notes")
    has_notes = notes_content is not None and notes_content != ""

    return TaskDetailOutput(task=task, notes_content=notes_content, has_notes=has_notes)


def convert_to_gantt_output(data: dict[str, Any]) -> GanttOutput:
    """Convert API response to GanttOutput.

    Args:
        data: API response data

    Returns:
        GanttOutput with Gantt chart data
    """
    # Convert date_range
    date_range = GanttDateRange(
        start_date=datetime.fromisoformat(data["date_range"]["start_date"]).date(),
        end_date=datetime.fromisoformat(data["date_range"]["end_date"]).date(),
    )

    # Convert tasks (list[GanttTaskResponse] -> list[GanttTaskDto])
    tasks = []
    for task in data["tasks"]:
        # Parse datetime fields using utility
        dt_fields = _parse_datetime_fields(
            task,
            ["planned_start", "planned_end", "actual_start", "actual_end", "deadline"],
        )

        tasks.append(
            GanttTaskDto(
                id=task["id"],
                name=task["name"],
                status=TaskStatus[task["status"].upper()],
                estimated_duration=task.get("estimated_duration"),
                planned_start=dt_fields["planned_start"],
                planned_end=dt_fields["planned_end"],
                actual_start=dt_fields["actual_start"],
                actual_end=dt_fields["actual_end"],
                deadline=dt_fields["deadline"],
                is_finished=task["status"].upper() in ["COMPLETED", "CANCELED"],
            )
        )

    # Convert task_daily_hours: dict[str, dict[str, float]] -> dict[int, dict[date, float]]
    task_daily_hours = {
        int(task_id): {
            datetime.fromisoformat(date_str).date(): hours
            for date_str, hours in daily_hours.items()
        }
        for task_id, daily_hours in data["task_daily_hours"].items()
    }

    # Convert daily_workload: dict[str, float] -> dict[date, float]
    daily_workload = {
        datetime.fromisoformat(date_str).date(): hours
        for date_str, hours in data["daily_workload"].items()
    }

    # Convert holidays: list[str] -> set[date]
    holidays = {
        datetime.fromisoformat(date_str).date() for date_str in data["holidays"]
    }

    return GanttOutput(
        date_range=date_range,
        tasks=tasks,
        task_daily_hours=task_daily_hours,
        daily_workload=daily_workload,
        holidays=holidays,
        total_estimated_duration=data.get("total_estimated_duration", 0.0),
    )


def _parse_task_statistics(completion_data: dict[str, Any]) -> TaskStatistics:
    """Parse task completion statistics from API response.

    Args:
        completion_data: Completion section from API response

    Returns:
        TaskStatistics object
    """
    return TaskStatistics(
        total_tasks=completion_data["total"],
        pending_count=completion_data["pending"],
        in_progress_count=completion_data["in_progress"],
        completed_count=completion_data["completed"],
        canceled_count=completion_data["canceled"],
        completion_rate=completion_data["completion_rate"],
    )


def _parse_time_statistics(time_data: dict[str, Any]) -> TimeStatistics:
    """Parse time tracking statistics from API response.

    Args:
        time_data: Time section from API response

    Returns:
        TimeStatistics object
    """
    return TimeStatistics(
        total_work_hours=time_data["total_logged_hours"],
        average_work_hours=time_data.get("average_task_duration") or 0.0,
        median_work_hours=0.0,  # Not available in API response
        longest_task=None,  # Not available in API response
        shortest_task=None,  # Not available in API response
        tasks_with_time_tracking=0,  # Not available in API response
    )


def _parse_estimation_statistics(
    estimation_data: dict[str, Any],
) -> EstimationAccuracyStatistics:
    """Parse estimation accuracy statistics from API response.

    Args:
        estimation_data: Estimation section from API response

    Returns:
        EstimationAccuracyStatistics object
    """
    return EstimationAccuracyStatistics(
        total_tasks_with_estimation=estimation_data["tasks_with_estimates"],
        accuracy_rate=estimation_data["average_deviation_percentage"] / 100,
        over_estimated_count=0,  # Not available in API response
        under_estimated_count=0,  # Not available in API response
        exact_count=0,  # Not available in API response
        best_estimated_tasks=[],  # Not available in API response
        worst_estimated_tasks=[],  # Not available in API response
    )


def _parse_deadline_statistics(
    deadline_data: dict[str, Any],
) -> DeadlineComplianceStatistics:
    """Parse deadline compliance statistics from API response.

    Args:
        deadline_data: Deadline section from API response

    Returns:
        DeadlineComplianceStatistics object
    """
    return DeadlineComplianceStatistics(
        total_tasks_with_deadline=deadline_data["met"] + deadline_data["missed"],
        met_deadline_count=deadline_data["met"],
        missed_deadline_count=deadline_data["missed"],
        compliance_rate=deadline_data["adherence_rate"],
        average_delay_days=0.0,  # Not available in API response
    )


def _parse_priority_statistics(
    priority_data: dict[str, Any],
) -> PriorityDistributionStatistics:
    """Parse priority distribution statistics from API response.

    Args:
        priority_data: Priority section from API response

    Returns:
        PriorityDistributionStatistics object
    """
    distribution = priority_data["distribution"]
    return PriorityDistributionStatistics(
        high_priority_count=sum(
            count for prio, count in distribution.items() if int(prio) >= 70
        ),
        medium_priority_count=sum(
            count for prio, count in distribution.items() if 30 <= int(prio) < 70
        ),
        low_priority_count=sum(
            count for prio, count in distribution.items() if int(prio) < 30
        ),
        high_priority_completion_rate=0.0,  # Not available in API response
        priority_completion_map={int(k): v for k, v in distribution.items()},
    )


def _parse_trend_statistics(trends_data: dict[str, Any]) -> TrendStatistics:
    """Parse trend statistics from API response.

    Args:
        trends_data: Trends section from API response

    Returns:
        TrendStatistics object
    """
    # Calculate last 7 and 30 days from completed_per_day
    completed_per_day = trends_data.get("completed_per_day", {})
    last_7_days = sum(list(completed_per_day.values())[-7:]) if completed_per_day else 0
    last_30_days = (
        sum(list(completed_per_day.values())[-30:]) if completed_per_day else 0
    )

    return TrendStatistics(
        last_7_days_completed=last_7_days,
        last_30_days_completed=last_30_days,
        weekly_completion_trend={},  # Would need grouping logic
        monthly_completion_trend={},  # Would need grouping logic
    )


def convert_to_statistics_output(data: dict[str, Any]) -> StatisticsOutput:
    """Convert API response to StatisticsOutput.

    Args:
        data: API response data with format:
            {
                "completion": {...},
                "time": {...} | None,
                "estimation": {...} | None,
                "deadline": {...} | None,
                "priority": {...},
                "trends": {...} | None
            }

    Returns:
        StatisticsOutput with converted data
    """
    # Parse each statistics section using helper functions
    task_stats = _parse_task_statistics(data["completion"])
    time_stats = _parse_time_statistics(data["time"]) if data.get("time") else None
    estimation_stats = (
        _parse_estimation_statistics(data["estimation"])
        if data.get("estimation")
        else None
    )
    deadline_stats = (
        _parse_deadline_statistics(data["deadline"]) if data.get("deadline") else None
    )
    priority_stats = _parse_priority_statistics(data["priority"])
    trend_stats = (
        _parse_trend_statistics(data["trends"]) if data.get("trends") else None
    )

    return StatisticsOutput(
        task_stats=task_stats,
        time_stats=time_stats,
        estimation_stats=estimation_stats,
        deadline_stats=deadline_stats,
        priority_stats=priority_stats,
        trend_stats=trend_stats,
    )


def _parse_optimization_summary(
    summary_data: dict[str, Any], failures: list[dict[str, Any]]
) -> OptimizationSummary:
    """Parse optimization summary from API response.

    Args:
        summary_data: Summary section from API response
        failures: Failures list from API response

    Returns:
        OptimizationSummary object
    """
    # Calculate days span from start_date and end_date
    start_date = date_type.fromisoformat(summary_data["start_date"])
    end_date = date_type.fromisoformat(summary_data["end_date"])
    days_span = (end_date - start_date).days + 1

    # Create TaskSummaryDto objects for unscheduled tasks from failures
    unscheduled_tasks = [
        TaskSummaryDto(id=f["task_id"], name=f["task_name"]) for f in failures
    ]

    return OptimizationSummary(
        new_count=summary_data["scheduled_tasks"],
        rescheduled_count=0,  # API doesn't distinguish between new and rescheduled
        total_hours=summary_data["total_hours"],
        deadline_conflicts=0,  # Not provided by API
        days_span=days_span,
        unscheduled_tasks=unscheduled_tasks,
        overloaded_days=[],  # Not provided by API
    )


def _parse_scheduling_failures(
    failures_data: list[dict[str, Any]],
) -> list[SchedulingFailure]:
    """Parse scheduling failures from API response.

    Args:
        failures_data: Failures list from API response

    Returns:
        List of SchedulingFailure objects
    """
    return [
        SchedulingFailure(
            task=TaskSummaryDto(id=f["task_id"], name=f["task_name"]),
            reason=f["reason"],
        )
        for f in failures_data
    ]


def convert_to_optimization_output(data: dict[str, Any]) -> OptimizationOutput:
    """Convert API response to OptimizationOutput.

    Args:
        data: API response data with format:
            {
                "summary": {
                    "total_tasks": int,
                    "scheduled_tasks": int,
                    "failed_tasks": int,
                    "total_hours": float,
                    "start_date": str (ISO),
                    "end_date": str (ISO),
                    "algorithm": str
                },
                "failures": [{
                    "task_id": int,
                    "task_name": str,
                    "reason": str
                }],
                "message": str
            }

    Returns:
        OptimizationOutput with all optimization results
    """
    summary = _parse_optimization_summary(data["summary"], data["failures"])
    failures = _parse_scheduling_failures(data["failures"])

    # Note: API response doesn't include successful_tasks details
    # We'll create minimal TaskSummaryDto objects
    successful_count = data["summary"]["scheduled_tasks"]
    successful_tasks = [
        TaskSummaryDto(id=i, name=f"Task {i}") for i in range(successful_count)
    ]

    # Daily allocations and task states not provided in response
    daily_allocations: dict[date_type, float] = {}
    task_states_before: dict[int, datetime | None] = {}

    return OptimizationOutput(
        successful_tasks=successful_tasks,
        failed_tasks=failures,
        daily_allocations=daily_allocations,
        summary=summary,
        task_states_before=task_states_before,
    )


def convert_to_tag_statistics_output(data: dict[str, Any]) -> TagStatisticsOutput:
    """Convert API response to TagStatisticsOutput.

    Args:
        data: API response data with format:
            {tags: [{tag: str, count: int, completion_rate: float}], total_tags: int}

    Returns:
        TagStatisticsOutput with tag statistics
    """
    # Convert to DTO: {tag_counts: dict[str, int], total_tags: int, total_tagged_tasks: int}
    tag_counts = {item["tag"]: item["count"] for item in data["tags"]}

    return TagStatisticsOutput(
        tag_counts=tag_counts,
        total_tags=data["total_tags"],
        total_tagged_tasks=0,  # Not available from API response
    )


def convert_to_simulation_result(data: dict[str, Any]) -> SimulationResult:
    """Convert API simulation response to SimulationResult DTO.

    Args:
        data: API response data with simulation results

    Returns:
        SimulationResult with schedule prediction and workload analysis
    """
    # Convert date string keys back to date objects
    daily_allocations = {}
    for date_str, hours in data.get("daily_allocations", {}).items():
        daily_allocations[date_type.fromisoformat(date_str)] = hours

    return SimulationResult(
        is_schedulable=data["is_schedulable"],
        planned_start=_parse_optional_datetime(data, "planned_start"),
        planned_end=_parse_optional_datetime(data, "planned_end"),
        failure_reason=data.get("failure_reason"),
        daily_allocations=daily_allocations,
        peak_workload=data["peak_workload"],
        peak_date=_parse_optional_date(data, "peak_date"),
        average_workload=data["average_workload"],
        total_workload_days=data["total_workload_days"],
        virtual_task_name=data["virtual_task_name"],
        estimated_duration=data["estimated_duration"],
        priority=data["priority"],
        deadline=_parse_optional_datetime(data, "deadline"),
    )
