"""Statistics data converters."""

from __future__ import annotations

from typing import NotRequired, TypedDict

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

# -- TypedDicts mirroring the server's JSON response shape ----------------


class TaskSummaryPayload(TypedDict):
    id: int
    name: str
    estimated_duration: NotRequired[float | None]
    actual_duration_hours: NotRequired[float | None]


class CompletionPayload(TypedDict):
    total: int
    completed: int
    in_progress: int
    pending: int
    canceled: int
    completion_rate: float


class TimePayload(TypedDict):
    total_work_hours: float
    average_work_hours: NotRequired[float | None]
    median_work_hours: NotRequired[float]
    longest_task: NotRequired[TaskSummaryPayload | None]
    shortest_task: NotRequired[TaskSummaryPayload | None]
    tasks_with_time_tracking: NotRequired[int]


class EstimationPayload(TypedDict):
    total_tasks_with_estimation: int
    accuracy_rate: NotRequired[float]
    over_estimated_count: NotRequired[int]
    under_estimated_count: NotRequired[int]
    exact_count: NotRequired[int]
    best_estimated_tasks: NotRequired[list[TaskSummaryPayload]]
    worst_estimated_tasks: NotRequired[list[TaskSummaryPayload]]


class DeadlinePayload(TypedDict):
    total_tasks_with_deadline: int
    met_deadline_count: int
    missed_deadline_count: int
    compliance_rate: float
    average_delay_days: NotRequired[float]


class PriorityPayload(TypedDict):
    distribution: dict[str, int]
    high_priority_count: NotRequired[int]
    medium_priority_count: NotRequired[int]
    low_priority_count: NotRequired[int]
    high_priority_completion_rate: NotRequired[float]


class TrendPayload(TypedDict, total=False):
    last_7_days_completed: int
    last_30_days_completed: int
    weekly_completion_trend: dict[str, int]
    monthly_completion_trend: dict[str, int]


class StatisticsPayload(TypedDict):
    completion: CompletionPayload
    time: NotRequired[TimePayload | None]
    estimation: NotRequired[EstimationPayload | None]
    deadline: NotRequired[DeadlinePayload | None]
    priority: PriorityPayload
    trends: NotRequired[TrendPayload | None]


# -- Converters -----------------------------------------------------------


def _parse_task_summary(data: TaskSummaryPayload | None) -> TaskSummaryDto | None:
    if data is None:
        return None
    return TaskSummaryDto(
        id=data["id"],
        name=data["name"],
        estimated_duration=data.get("estimated_duration"),
        actual_duration_hours=data.get("actual_duration_hours"),
    )


def _parse_task_summary_list(
    data: list[TaskSummaryPayload] | None,
) -> list[TaskSummaryDto]:
    if not data:
        return []
    return [
        TaskSummaryDto(
            id=d["id"],
            name=d["name"],
            estimated_duration=d.get("estimated_duration"),
            actual_duration_hours=d.get("actual_duration_hours"),
        )
        for d in data
    ]


def _parse_task_statistics(data: CompletionPayload) -> TaskStatistics:
    return TaskStatistics(
        total_tasks=data["total"],
        pending_count=data["pending"],
        in_progress_count=data["in_progress"],
        completed_count=data["completed"],
        canceled_count=data["canceled"],
        completion_rate=data["completion_rate"],
    )


def _parse_time_statistics(data: TimePayload) -> TimeStatistics:
    return TimeStatistics(
        total_work_hours=data["total_work_hours"],
        average_work_hours=data.get("average_work_hours") or 0.0,
        median_work_hours=data.get("median_work_hours", 0.0),
        longest_task=_parse_task_summary(data.get("longest_task")),
        shortest_task=_parse_task_summary(data.get("shortest_task")),
        tasks_with_time_tracking=data.get("tasks_with_time_tracking", 0),
    )


def _parse_estimation_statistics(
    data: EstimationPayload,
) -> EstimationAccuracyStatistics:
    return EstimationAccuracyStatistics(
        total_tasks_with_estimation=data["total_tasks_with_estimation"],
        accuracy_rate=data.get("accuracy_rate", 0.0),
        over_estimated_count=data.get("over_estimated_count", 0),
        under_estimated_count=data.get("under_estimated_count", 0),
        exact_count=data.get("exact_count", 0),
        best_estimated_tasks=_parse_task_summary_list(data.get("best_estimated_tasks")),
        worst_estimated_tasks=_parse_task_summary_list(
            data.get("worst_estimated_tasks")
        ),
    )


def _parse_deadline_statistics(data: DeadlinePayload) -> DeadlineComplianceStatistics:
    return DeadlineComplianceStatistics(
        total_tasks_with_deadline=data["total_tasks_with_deadline"],
        met_deadline_count=data["met_deadline_count"],
        missed_deadline_count=data["missed_deadline_count"],
        compliance_rate=data["compliance_rate"],
        average_delay_days=data.get("average_delay_days", 0.0),
    )


def _parse_priority_statistics(
    data: PriorityPayload,
) -> PriorityDistributionStatistics:
    distribution = data["distribution"]
    return PriorityDistributionStatistics(
        high_priority_count=data.get("high_priority_count", 0),
        medium_priority_count=data.get("medium_priority_count", 0),
        low_priority_count=data.get("low_priority_count", 0),
        high_priority_completion_rate=data.get("high_priority_completion_rate", 0.0),
        priority_completion_map={int(k): v for k, v in distribution.items()},
    )


def _parse_trend_statistics(data: TrendPayload) -> TrendStatistics:
    return TrendStatistics(
        last_7_days_completed=data.get("last_7_days_completed", 0),
        last_30_days_completed=data.get("last_30_days_completed", 0),
        weekly_completion_trend=data.get("weekly_completion_trend", {}),
        monthly_completion_trend=data.get("monthly_completion_trend", {}),
    )


def convert_to_statistics_output(data: StatisticsPayload) -> StatisticsOutput:
    """Convert API response to StatisticsOutput."""
    task_stats = _parse_task_statistics(data["completion"])
    priority_stats = _parse_priority_statistics(data["priority"])

    raw_time = data.get("time")
    raw_estimation = data.get("estimation")
    raw_deadline = data.get("deadline")
    raw_trends = data.get("trends")

    return StatisticsOutput(
        task_stats=task_stats,
        time_stats=_parse_time_statistics(raw_time) if raw_time else None,
        estimation_stats=(
            _parse_estimation_statistics(raw_estimation) if raw_estimation else None
        ),
        deadline_stats=(
            _parse_deadline_statistics(raw_deadline) if raw_deadline else None
        ),
        priority_stats=priority_stats,
        trend_stats=_parse_trend_statistics(raw_trends) if raw_trends else None,
    )
