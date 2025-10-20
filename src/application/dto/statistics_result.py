"""Statistics result DTOs for task analysis."""

from dataclasses import dataclass

from domain.entities.task import Task


@dataclass
class TaskStatistics:
    """Basic task statistics.

    Attributes:
        total_tasks: Total number of tasks
        pending_count: Number of pending tasks
        in_progress_count: Number of in-progress tasks
        completed_count: Number of completed tasks
        canceled_count: Number of canceled tasks
        completion_rate: Completion rate (completed / (completed + canceled))
    """

    total_tasks: int
    pending_count: int
    in_progress_count: int
    completed_count: int
    canceled_count: int
    completion_rate: float


@dataclass
class TimeStatistics:
    """Time tracking statistics.

    Attributes:
        total_work_hours: Total work hours across all completed tasks
        average_work_hours: Average work hours per completed task
        median_work_hours: Median work hours per completed task
        longest_task: Task with the longest actual duration
        shortest_task: Task with the shortest actual duration
        tasks_with_time_tracking: Number of tasks with time tracking data
    """

    total_work_hours: float
    average_work_hours: float
    median_work_hours: float
    longest_task: Task | None
    shortest_task: Task | None
    tasks_with_time_tracking: int


@dataclass
class EstimationAccuracyStatistics:
    """Estimation accuracy statistics.

    Attributes:
        total_tasks_with_estimation: Number of tasks with both estimation and actual duration
        accuracy_rate: Average accuracy (actual / estimated)
        over_estimated_count: Number of tasks finished faster than estimated
        under_estimated_count: Number of tasks that took longer than estimated
        exact_count: Number of tasks with accurate estimation (±10%)
        best_estimated_tasks: Top 3 tasks with best estimation accuracy
        worst_estimated_tasks: Top 3 tasks with worst estimation accuracy
    """

    total_tasks_with_estimation: int
    accuracy_rate: float
    over_estimated_count: int
    under_estimated_count: int
    exact_count: int
    best_estimated_tasks: list[Task]
    worst_estimated_tasks: list[Task]


@dataclass
class DeadlineComplianceStatistics:
    """Deadline compliance statistics.

    Attributes:
        total_tasks_with_deadline: Number of completed tasks with deadline
        met_deadline_count: Number of tasks completed before or on deadline
        missed_deadline_count: Number of tasks completed after deadline
        compliance_rate: Compliance rate (met / total)
        average_delay_days: Average delay in days for missed deadlines
    """

    total_tasks_with_deadline: int
    met_deadline_count: int
    missed_deadline_count: int
    compliance_rate: float
    average_delay_days: float


@dataclass
class PriorityDistributionStatistics:
    """Priority distribution statistics.

    Attributes:
        high_priority_count: Number of high priority tasks (>= 70)
        medium_priority_count: Number of medium priority tasks (30-69)
        low_priority_count: Number of low priority tasks (< 30)
        high_priority_completion_rate: Completion rate for high priority tasks
        priority_completion_map: Map of priority value to completed count
    """

    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    high_priority_completion_rate: float
    priority_completion_map: dict[int, int]


@dataclass
class TrendStatistics:
    """Trend statistics over time.

    Attributes:
        last_7_days_completed: Number of tasks completed in last 7 days
        last_30_days_completed: Number of tasks completed in last 30 days
        weekly_completion_trend: Weekly completion counts (week_start -> count)
        monthly_completion_trend: Monthly completion counts (month -> count)
    """

    last_7_days_completed: int
    last_30_days_completed: int
    weekly_completion_trend: dict[str, int]
    monthly_completion_trend: dict[str, int]


@dataclass
class StatisticsResult:
    """Complete statistics result.

    Attributes:
        task_stats: Basic task statistics
        time_stats: Time tracking statistics (None if no time data)
        estimation_stats: Estimation accuracy statistics (None if no estimation data)
        deadline_stats: Deadline compliance statistics (None if no deadline data)
        priority_stats: Priority distribution statistics
        trend_stats: Trend statistics (None if period is not 'all')
    """

    task_stats: TaskStatistics
    time_stats: TimeStatistics | None
    estimation_stats: EstimationAccuracyStatistics | None
    deadline_stats: DeadlineComplianceStatistics | None
    priority_stats: PriorityDistributionStatistics
    trend_stats: TrendStatistics | None


@dataclass
class CalculateStatisticsRequest:
    """Input for calculate statistics use case.

    Attributes:
        period: Time period for filtering ('7d', '30d', or 'all')
    """

    period: str = "all"
