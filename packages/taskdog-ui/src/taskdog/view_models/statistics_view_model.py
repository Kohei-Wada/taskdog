"""ViewModels for Statistics presentation.

These ViewModels contain only the data needed for rendering statistics,
without domain entity references. All presentation logic (formatting,
calculations) is applied by the Mapper.
"""

from dataclasses import dataclass

from taskdog.view_models.base import BaseViewModel
from taskdog_core.application.dto.statistics_output import (
    DeadlineComplianceStatistics,
    PriorityDistributionStatistics,
    TaskStatistics,
    TrendStatistics,
)


@dataclass(frozen=True)
class TaskSummaryViewModel(BaseViewModel):
    """ViewModel for task summary in statistics display.

    This is a lightweight representation of a task containing only
    the fields needed for statistics rendering.

    Attributes:
        id: Task ID
        name: Task name
        estimated_duration: Estimated duration in hours (None if not set)
        actual_duration_hours: Actual duration in hours (None if not set)
    """

    id: int
    name: str
    estimated_duration: float | None
    actual_duration_hours: float | None


@dataclass(frozen=True)
class TimeStatisticsViewModel(BaseViewModel):
    """ViewModel for time tracking statistics.

    Attributes:
        total_work_hours: Total work hours across all completed tasks
        average_work_hours: Average work hours per completed task
        median_work_hours: Median work hours per completed task
        longest_task: Task summary with the longest actual duration
        shortest_task: Task summary with the shortest actual duration
        tasks_with_time_tracking: Number of tasks with time tracking data
    """

    total_work_hours: float
    average_work_hours: float
    median_work_hours: float
    longest_task: TaskSummaryViewModel | None
    shortest_task: TaskSummaryViewModel | None
    tasks_with_time_tracking: int


@dataclass(frozen=True)
class EstimationAccuracyStatisticsViewModel(BaseViewModel):
    """ViewModel for estimation accuracy statistics.

    Attributes:
        total_tasks_with_estimation: Number of tasks with both estimation and actual duration
        accuracy_rate: Average accuracy (actual / estimated)
        over_estimated_count: Number of tasks finished faster than estimated
        under_estimated_count: Number of tasks that took longer than estimated
        exact_count: Number of tasks with accurate estimation (±10%)
        best_estimated_tasks: Top tasks with best estimation accuracy
        worst_estimated_tasks: Top tasks with worst estimation accuracy
    """

    total_tasks_with_estimation: int
    accuracy_rate: float
    over_estimated_count: int
    under_estimated_count: int
    exact_count: int
    best_estimated_tasks: list[TaskSummaryViewModel]
    worst_estimated_tasks: list[TaskSummaryViewModel]


@dataclass(frozen=True)
class StatisticsViewModel(BaseViewModel):
    """ViewModel for complete statistics result.

    This is the presentation-ready version of StatisticsOutput, containing
    ViewModels instead of Task entities.

    Note: TaskStatistics, DeadlineComplianceStatistics, PriorityDistributionStatistics,
    and TrendStatistics don't contain Task entities, so they are used directly
    without conversion.

    Attributes:
        task_stats: Basic task statistics (from DTO, no conversion needed)
        time_stats: Time tracking statistics ViewModel
        estimation_stats: Estimation accuracy statistics ViewModel
        deadline_stats: Deadline compliance statistics (from DTO, no conversion needed)
        priority_stats: Priority distribution statistics (from DTO, no conversion needed)
        trend_stats: Trend statistics (from DTO, no conversion needed)
    """

    task_stats: TaskStatistics
    time_stats: TimeStatisticsViewModel | None
    estimation_stats: EstimationAccuracyStatisticsViewModel | None
    deadline_stats: DeadlineComplianceStatistics | None
    priority_stats: PriorityDistributionStatistics
    trend_stats: TrendStatistics | None
