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
