"""Statistics result DTOs for task analysis."""

from dataclasses import dataclass

from pydantic import BaseModel

from taskdog_core.application.dto.task_dto import TaskSummaryDto


class TaskStatistics(BaseModel):
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


class TimeStatistics(BaseModel):
    """Time tracking statistics.

    Attributes:
        total_work_hours: Total work hours across all completed tasks
        average_work_hours: Average work hours per completed task
        median_work_hours: Median work hours per completed task
        longest_task: Basic info of task with the longest actual duration
        shortest_task: Basic info of task with the shortest actual duration
        tasks_with_time_tracking: Number of tasks with time tracking data
    """

    total_work_hours: float
    average_work_hours: float
    median_work_hours: float
    longest_task: TaskSummaryDto | None
    shortest_task: TaskSummaryDto | None
    tasks_with_time_tracking: int


class EstimationAccuracyStatistics(BaseModel):
    """Estimation accuracy statistics.

    Attributes:
        total_tasks_with_estimation: Number of tasks with both estimation and actual duration
        accuracy_rate: Average accuracy (actual / estimated)
        over_estimated_count: Number of tasks finished faster than estimated
        under_estimated_count: Number of tasks that took longer than estimated
        exact_count: Number of tasks with accurate estimation (±10%)
        best_estimated_tasks: Top 3 tasks with best estimation accuracy (basic info)
        worst_estimated_tasks: Top 3 tasks with worst estimation accuracy (basic info)
    """

    total_tasks_with_estimation: int
    accuracy_rate: float
    over_estimated_count: int
    under_estimated_count: int
    exact_count: int
    best_estimated_tasks: list[TaskSummaryDto]
    worst_estimated_tasks: list[TaskSummaryDto]
    estimation_pairs: list[tuple[float, float]] = []


class DeadlineComplianceStatistics(BaseModel):
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


class PriorityDistributionStatistics(BaseModel):
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


class TrendStatistics(BaseModel):
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


class ActivityPatternStatistics(BaseModel):
    """Activity pattern statistics based on task completion times.

    Attributes:
        hourly_completions: Completion count per hour (0-23)
        daily_completions: Completion count per day of week (0=Mon, 6=Sun)
        heatmap: 7x24 matrix of completion counts (day_of_week x hour)
        total_completed_with_time: Number of tasks with completion time data
    """

    hourly_completions: dict[int, int]
    daily_completions: dict[int, int]
    heatmap: dict[int, dict[int, int]]
    total_completed_with_time: int


class LeadTimeBreakdown(BaseModel):
    """Reschedule likelihood grouped by planning lead time.

    Lead time is the distance between the moment a deadline was first set
    and the deadline itself.

    Attributes:
        category: Lead time bucket ('same_day', '1_2_days', '3_7_days', '8_plus_days')
        task_count: Number of tasks in this bucket
        rescheduled_count: Number of those tasks that were rescheduled at least once
        reschedule_rate: rescheduled_count / task_count
    """

    category: str
    task_count: int
    rescheduled_count: int
    reschedule_rate: float


class ChronicSlipperTask(BaseModel):
    """A task whose deadline was rescheduled repeatedly.

    Attributes:
        task_id: Task ID
        task_name: Task name (from the latest audit entry)
        reschedule_count: Number of deadline reschedules
        total_slip_days: Net days the deadline moved (positive = pushed later)
        first_deadline: Earliest recorded deadline (ISO format)
        latest_deadline: Latest recorded deadline (ISO format)
    """

    task_id: int
    task_name: str
    reschedule_count: int
    total_slip_days: float
    first_deadline: str
    latest_deadline: str


class RescheduleStatistics(BaseModel):
    """Deadline rescheduling statistics derived from the audit log.

    Only tasks that appear in the audit log are counted, so tasks created
    before audit logging was enabled are invisible to these statistics.

    Attributes:
        tasks_with_deadline: Distinct tasks with any deadline event in the period
        rescheduled_task_count: Distinct tasks with at least one reschedule
        total_reschedule_events: Total deadline reschedules (value-to-value changes)
        reschedule_rate: rescheduled_task_count / tasks_with_deadline
        moved_earlier_count: Reschedules that moved the deadline earlier
        lead_time_breakdown: Reschedule likelihood per planning lead time bucket
        chronic_slippers: Tasks with 3+ reschedules, worst first
        weekly_reschedule_trend: Reschedule counts per ISO week (e.g. '2026-W28')
    """

    tasks_with_deadline: int
    rescheduled_task_count: int
    total_reschedule_events: int
    reschedule_rate: float
    moved_earlier_count: int
    lead_time_breakdown: list[LeadTimeBreakdown]
    chronic_slippers: list[ChronicSlipperTask]
    weekly_reschedule_trend: dict[str, int]


class StatisticsOutput(BaseModel):
    """Complete statistics result.

    Attributes:
        task_stats: Basic task statistics
        time_stats: Time tracking statistics (None if no time data)
        estimation_stats: Estimation accuracy statistics (None if no estimation data)
        deadline_stats: Deadline compliance statistics (None if no deadline data)
        priority_stats: Priority distribution statistics
        trend_stats: Trend statistics (None if period is not 'all')
        activity_stats: Activity pattern statistics (None if no completion time data)
        reschedule_stats: Deadline reschedule statistics (None if audit data unavailable)
    """

    task_stats: TaskStatistics
    time_stats: TimeStatistics | None
    estimation_stats: EstimationAccuracyStatistics | None
    deadline_stats: DeadlineComplianceStatistics | None
    priority_stats: PriorityDistributionStatistics
    trend_stats: TrendStatistics | None
    activity_stats: ActivityPatternStatistics | None = None
    reschedule_stats: RescheduleStatistics | None = None


@dataclass
class CalculateStatisticsInput:
    """Input for calculate statistics use case.

    Attributes:
        period: Time period for filtering ('7d', '30d', or 'all')
    """

    period: str = "all"
