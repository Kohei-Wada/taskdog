"""Statistics data converters."""

from typing import Any

from taskdog_core.application.dto.statistics_output import (
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from taskdog_core.application.dto.task_dto import TaskSummaryDto


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


def _parse_task_summary(data: dict[str, Any] | None) -> TaskSummaryDto | None:
    """Parse task summary from API response.

    Args:
        data: Task summary data from API response

    Returns:
        TaskSummaryDto or None
    """
    if data is None:
        return None
    return TaskSummaryDto(
        id=data["id"],
        name=data["name"],
        estimated_duration=data.get("estimated_duration"),
        actual_duration_hours=data.get("actual_duration_hours"),
    )


def _parse_task_summary_list(data: list[dict[str, Any]] | None) -> list[TaskSummaryDto]:
    """Parse list of task summaries from API response.

    Args:
        data: List of task summary data from API response

    Returns:
        List of TaskSummaryDto
    """
    if not data:
        return []
    # Each element d is a dict (never None), so _parse_task_summary always returns TaskSummaryDto
    return [_parse_task_summary(d) for d in data]  # type: ignore[misc]


def _parse_time_statistics(time_data: dict[str, Any]) -> TimeStatistics:
    """Parse time tracking statistics from API response.

    Args:
        time_data: Time section from API response

    Returns:
        TimeStatistics object
    """
    return TimeStatistics(
        total_work_hours=time_data["total_work_hours"],
        average_work_hours=time_data.get("average_work_hours") or 0.0,
        median_work_hours=time_data.get("median_work_hours", 0.0),
        longest_task=_parse_task_summary(time_data.get("longest_task")),
        shortest_task=_parse_task_summary(time_data.get("shortest_task")),
        tasks_with_time_tracking=time_data.get("tasks_with_time_tracking", 0),
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
        total_tasks_with_estimation=estimation_data["total_tasks_with_estimation"],
        accuracy_rate=estimation_data.get("accuracy_rate", 0.0),
        over_estimated_count=estimation_data.get("over_estimated_count", 0),
        under_estimated_count=estimation_data.get("under_estimated_count", 0),
        exact_count=estimation_data.get("exact_count", 0),
        best_estimated_tasks=_parse_task_summary_list(
            estimation_data.get("best_estimated_tasks")
        ),
        worst_estimated_tasks=_parse_task_summary_list(
            estimation_data.get("worst_estimated_tasks")
        ),
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
        total_tasks_with_deadline=deadline_data["total_tasks_with_deadline"],
        met_deadline_count=deadline_data["met_deadline_count"],
        missed_deadline_count=deadline_data["missed_deadline_count"],
        compliance_rate=deadline_data["compliance_rate"],
        average_delay_days=deadline_data.get("average_delay_days", 0.0),
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
        high_priority_count=priority_data.get("high_priority_count", 0),
        medium_priority_count=priority_data.get("medium_priority_count", 0),
        low_priority_count=priority_data.get("low_priority_count", 0),
        high_priority_completion_rate=priority_data.get(
            "high_priority_completion_rate", 0.0
        ),
        priority_completion_map={int(k): v for k, v in distribution.items()},
    )


def _parse_trend_statistics(trends_data: dict[str, Any]) -> TrendStatistics:
    """Parse trend statistics from API response.

    Args:
        trends_data: Trends section from API response

    Returns:
        TrendStatistics object
    """
    return TrendStatistics(
        last_7_days_completed=trends_data.get("last_7_days_completed", 0),
        last_30_days_completed=trends_data.get("last_30_days_completed", 0),
        weekly_completion_trend=trends_data.get("weekly_completion_trend", {}),
        monthly_completion_trend=trends_data.get("monthly_completion_trend", {}),
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
