"""DTO converters for API responses.

Converts JSON responses from API to taskdog-core DTOs.
Single source of truth for all API-to-DTO transformations.
"""

from datetime import date as date_type
from datetime import datetime
from typing import Any

from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import GetTaskByIdOutput
from taskdog_core.application.dto.optimization_output import (
    OptimizationOutput,
    SchedulingFailure,
)
from taskdog_core.application.dto.optimization_summary import OptimizationSummary
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
from taskdog_core.application.dto.task_detail_output import GetTaskDetailOutput
from taskdog_core.application.dto.task_dto import (
    GanttTaskDto,
    TaskDetailDto,
    TaskRowDto,
    TaskSummaryDto,
)
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import UpdateTaskOutput
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


def convert_to_update_task_output(data: dict[str, Any]) -> UpdateTaskOutput:
    """Convert API response to UpdateTaskOutput.

    Args:
        data: API response data

    Returns:
        UpdateTaskOutput with updated task data and fields
    """
    # Reuse convert_to_task_operation_output to avoid duplication
    task = convert_to_task_operation_output(data)

    # Construct UpdateTaskOutput with nested task and updated_fields
    return UpdateTaskOutput(
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


def convert_to_get_task_by_id_output(data: dict[str, Any]) -> GetTaskByIdOutput:
    """Convert API response to GetTaskByIdOutput.

    Args:
        data: API response data

    Returns:
        GetTaskByIdOutput with task data
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

    return GetTaskByIdOutput(task=task)


def convert_to_get_task_detail_output(data: dict[str, Any]) -> GetTaskDetailOutput:
    """Convert API response to GetTaskDetailOutput.

    Args:
        data: API response data

    Returns:
        GetTaskDetailOutput with task data and notes
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

    return GetTaskDetailOutput(
        task=task, notes_content=notes_content, has_notes=has_notes
    )


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
    # Convert completion statistics (always present)
    completion = data["completion"]
    task_stats = TaskStatistics(
        total_tasks=completion["total"],
        pending_count=completion["pending"],
        in_progress_count=completion["in_progress"],
        completed_count=completion["completed"],
        canceled_count=completion["canceled"],
        completion_rate=completion["completion_rate"],
    )

    # Convert time statistics (optional)
    time_stats = None
    if data.get("time"):
        time = data["time"]
        time_stats = TimeStatistics(
            total_work_hours=time["total_logged_hours"],
            average_work_hours=time.get("average_task_duration") or 0.0,
            median_work_hours=0.0,  # Not available in API response
            longest_task=None,  # Not available in API response
            shortest_task=None,  # Not available in API response
            tasks_with_time_tracking=0,  # Not available in API response
        )

    # Convert estimation statistics (optional)
    estimation_stats = None
    if data.get("estimation"):
        estimation = data["estimation"]
        estimation_stats = EstimationAccuracyStatistics(
            total_tasks_with_estimation=estimation["tasks_with_estimates"],
            accuracy_rate=estimation["average_deviation_percentage"] / 100,
            over_estimated_count=0,  # Not available in API response
            under_estimated_count=0,  # Not available in API response
            exact_count=0,  # Not available in API response
            best_estimated_tasks=[],  # Not available in API response
            worst_estimated_tasks=[],  # Not available in API response
        )

    # Convert deadline statistics (optional)
    deadline_stats = None
    if data.get("deadline"):
        deadline = data["deadline"]
        deadline_stats = DeadlineComplianceStatistics(
            total_tasks_with_deadline=deadline["met"] + deadline["missed"],
            met_deadline_count=deadline["met"],
            missed_deadline_count=deadline["missed"],
            compliance_rate=deadline["adherence_rate"],
            average_delay_days=0.0,  # Not available in API response
        )

    # Convert priority statistics (always present)
    priority = data["priority"]
    priority_stats = PriorityDistributionStatistics(
        high_priority_count=sum(
            count for prio, count in priority["distribution"].items() if int(prio) >= 70
        ),
        medium_priority_count=sum(
            count
            for prio, count in priority["distribution"].items()
            if 30 <= int(prio) < 70
        ),
        low_priority_count=sum(
            count for prio, count in priority["distribution"].items() if int(prio) < 30
        ),
        high_priority_completion_rate=0.0,  # Not available in API response
        priority_completion_map={
            int(k): v for k, v in priority["distribution"].items()
        },
    )

    # Convert trend statistics (optional)
    trend_stats = None
    if data.get("trends"):
        trends = data["trends"]
        # Calculate last 7 and 30 days from completed_per_day
        completed_per_day = trends.get("completed_per_day", {})
        last_7_days = (
            sum(list(completed_per_day.values())[-7:]) if completed_per_day else 0
        )
        last_30_days = (
            sum(list(completed_per_day.values())[-30:]) if completed_per_day else 0
        )

        trend_stats = TrendStatistics(
            last_7_days_completed=last_7_days,
            last_30_days_completed=last_30_days,
            weekly_completion_trend={},  # Would need grouping logic
            monthly_completion_trend={},  # Would need grouping logic
        )

    return StatisticsOutput(
        task_stats=task_stats,
        time_stats=time_stats,
        estimation_stats=estimation_stats,
        deadline_stats=deadline_stats,
        priority_stats=priority_stats,
        trend_stats=trend_stats,
    )


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
    # Parse summary
    summary_data = data["summary"]

    # Calculate days span from start_date and end_date
    start_date = date_type.fromisoformat(summary_data["start_date"])
    end_date = date_type.fromisoformat(summary_data["end_date"])
    days_span = (end_date - start_date).days + 1

    # Create TaskSummaryDto objects for unscheduled tasks from failures
    unscheduled_tasks = [
        TaskSummaryDto(id=f["task_id"], name=f["task_name"]) for f in data["failures"]
    ]

    summary = OptimizationSummary(
        new_count=summary_data["scheduled_tasks"],
        rescheduled_count=0,  # API doesn't distinguish between new and rescheduled
        total_hours=summary_data["total_hours"],
        deadline_conflicts=0,  # Not provided by API
        days_span=days_span,
        unscheduled_tasks=unscheduled_tasks,
        overloaded_days=[],  # Not provided by API
    )

    # Parse failures
    failures = [
        SchedulingFailure(
            task=TaskSummaryDto(id=f["task_id"], name=f["task_name"]),
            reason=f["reason"],
        )
        for f in data["failures"]
    ]

    # Note: API response doesn't include successful_tasks details
    # We'll create minimal TaskSummaryDto objects
    successful_count = summary_data["scheduled_tasks"]
    successful_tasks = [
        TaskSummaryDto(id=i, name=f"Task {i}") for i in range(successful_count)
    ]

    # Daily allocations - not provided in response, use empty dict
    daily_allocations: dict[date_type, float] = {}

    # Task states before - not provided in response, use empty dict
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
