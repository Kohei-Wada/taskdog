"""Service for calculating task statistics."""

from collections import defaultdict
from datetime import datetime, timedelta

from application.dto.statistics_result import (
    DeadlineComplianceStatistics,
    EstimationAccuracyStatistics,
    PriorityDistributionStatistics,
    StatisticsResult,
    TaskStatistics,
    TimeStatistics,
    TrendStatistics,
)
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task, TaskStatus


class TaskStatisticsCalculator:
    """Calculator for task statistics.

    This service analyzes task data and calculates various statistics
    including basic counts, time tracking, estimation accuracy, deadline
    compliance, priority distribution, and trends.
    """

    # Priority thresholds
    HIGH_PRIORITY_THRESHOLD = 70
    LOW_PRIORITY_THRESHOLD = 30

    # Estimation accuracy tolerance (±10%)
    ESTIMATION_TOLERANCE = 0.1

    def calculate_all(self, tasks: list[Task], period: str = "all") -> StatisticsResult:
        """Calculate all statistics for the given tasks.

        Args:
            tasks: List of tasks to analyze
            period: Time period filter ('7d', '30d', or 'all')

        Returns:
            StatisticsResult containing all calculated statistics
        """
        # Filter tasks by period if needed
        filtered_tasks = self._filter_by_period(tasks, period) if period != "all" else tasks

        # Calculate each statistics section
        task_stats = self._calculate_task_statistics(filtered_tasks)
        time_stats = self._calculate_time_statistics(filtered_tasks)
        estimation_stats = self._calculate_estimation_accuracy(filtered_tasks)
        deadline_stats = self._calculate_deadline_compliance(filtered_tasks)
        priority_stats = self._calculate_priority_distribution(filtered_tasks)
        trend_stats = self._calculate_trends(filtered_tasks) if period == "all" else None

        return StatisticsResult(
            task_stats=task_stats,
            time_stats=time_stats,
            estimation_stats=estimation_stats,
            deadline_stats=deadline_stats,
            priority_stats=priority_stats,
            trend_stats=trend_stats,
        )

    def _filter_by_period(self, tasks: list[Task], period: str) -> list[Task]:
        """Filter tasks by time period.

        Args:
            tasks: List of tasks to filter
            period: Time period ('7d' or '30d')

        Returns:
            Filtered list of tasks
        """
        now = datetime.now()
        days = 7 if period == "7d" else 30
        cutoff = now - timedelta(days=days)

        filtered = []
        for task in tasks:
            # Include tasks that were completed within the period
            if task.actual_end:
                end_dt = datetime.strptime(task.actual_end, DATETIME_FORMAT)
                if end_dt >= cutoff:
                    filtered.append(task)
            # Also include active tasks (PENDING, IN_PROGRESS)
            elif task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                filtered.append(task)

        return filtered

    def _calculate_task_statistics(self, tasks: list[Task]) -> TaskStatistics:
        """Calculate basic task statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            TaskStatistics with basic counts and completion rate
        """
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        canceled = sum(1 for t in tasks if t.status == TaskStatus.CANCELED)

        # Calculate completion rate
        finished_tasks = completed + canceled
        completion_rate = (completed / finished_tasks) if finished_tasks > 0 else 0.0

        return TaskStatistics(
            total_tasks=len(tasks),
            pending_count=pending,
            in_progress_count=in_progress,
            completed_count=completed,
            canceled_count=canceled,
            completion_rate=completion_rate,
        )

    def _calculate_time_statistics(self, tasks: list[Task]) -> TimeStatistics | None:
        """Calculate time tracking statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            TimeStatistics or None if no time tracking data
        """
        # Get tasks with actual duration
        tasks_with_duration = [t for t in tasks if t.actual_duration_hours is not None]

        if not tasks_with_duration:
            return None

        # Extract durations (guaranteed to be float, not None)
        durations: list[float] = [
            t.actual_duration_hours
            for t in tasks_with_duration
            if t.actual_duration_hours is not None
        ]
        total_hours = sum(durations)
        avg_hours = total_hours / len(durations)

        # Calculate median
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        if n % 2 == 0:
            median_hours = (sorted_durations[n // 2 - 1] + sorted_durations[n // 2]) / 2
        else:
            median_hours = sorted_durations[n // 2]

        # Find longest and shortest tasks
        longest_task = max(tasks_with_duration, key=lambda t: t.actual_duration_hours or 0.0)
        shortest_task = min(tasks_with_duration, key=lambda t: t.actual_duration_hours or 0.0)

        return TimeStatistics(
            total_work_hours=round(total_hours, 1),
            average_work_hours=round(avg_hours, 1),
            median_work_hours=round(median_hours, 1),
            longest_task=longest_task,
            shortest_task=shortest_task,
            tasks_with_time_tracking=len(tasks_with_duration),
        )

    def _calculate_estimation_accuracy(
        self, tasks: list[Task]
    ) -> EstimationAccuracyStatistics | None:
        """Calculate estimation accuracy statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            EstimationAccuracyStatistics or None if no estimation data
        """
        # Get tasks with both estimation and actual duration
        estimated_tasks = [
            t
            for t in tasks
            if t.estimated_duration is not None and t.actual_duration_hours is not None
        ]

        if not estimated_tasks:
            return None

        # Calculate accuracy rates
        accuracy_rates = []
        over_estimated = 0
        under_estimated = 0
        exact = 0

        for task in estimated_tasks:
            # Type guard: both are guaranteed to be non-None due to filter
            if task.actual_duration_hours is None or task.estimated_duration is None:
                continue

            rate = task.actual_duration_hours / task.estimated_duration
            accuracy_rates.append(rate)

            # Classify estimation accuracy
            if rate < (1 - self.ESTIMATION_TOLERANCE):
                # Finished faster than estimated (over-estimated)
                over_estimated += 1
            elif rate > (1 + self.ESTIMATION_TOLERANCE):
                # Took longer than estimated (under-estimated)
                under_estimated += 1
            else:
                # Within tolerance (±10%)
                exact += 1

        avg_accuracy = sum(accuracy_rates) / len(accuracy_rates)

        # Find best and worst estimated tasks
        # Best = closest to 1.0 (actual ≈ estimated)
        # Worst = farthest from 1.0
        tasks_with_accuracy = [
            (
                task,
                abs((task.actual_duration_hours or 0.0) / (task.estimated_duration or 1.0) - 1.0),
            )
            for task in estimated_tasks
            if task.actual_duration_hours is not None and task.estimated_duration is not None
        ]
        tasks_with_accuracy.sort(key=lambda x: x[1])

        best_tasks = [t[0] for t in tasks_with_accuracy[:3]]
        worst_tasks = [t[0] for t in tasks_with_accuracy[-3:][::-1]]

        return EstimationAccuracyStatistics(
            total_tasks_with_estimation=len(estimated_tasks),
            accuracy_rate=round(avg_accuracy, 2),
            over_estimated_count=over_estimated,
            under_estimated_count=under_estimated,
            exact_count=exact,
            best_estimated_tasks=best_tasks,
            worst_estimated_tasks=worst_tasks,
        )

    def _calculate_deadline_compliance(
        self, tasks: list[Task]
    ) -> DeadlineComplianceStatistics | None:
        """Calculate deadline compliance statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            DeadlineComplianceStatistics or None if no deadline data
        """
        # Get completed tasks with deadline
        tasks_with_deadline = [
            t
            for t in tasks
            if t.deadline is not None and t.actual_end is not None and t.is_finished
        ]

        if not tasks_with_deadline:
            return None

        met_count = 0
        missed_count = 0
        total_delay_days = 0.0

        for task in tasks_with_deadline:
            # Type guard: both are guaranteed to be non-None due to filter
            if task.deadline is None or task.actual_end is None:
                continue

            deadline_dt = datetime.strptime(task.deadline, DATETIME_FORMAT)
            actual_end_dt = datetime.strptime(task.actual_end, DATETIME_FORMAT)

            if actual_end_dt <= deadline_dt:
                met_count += 1
            else:
                missed_count += 1
                delay_days = (actual_end_dt - deadline_dt).total_seconds() / 86400
                total_delay_days += delay_days

        compliance_rate = met_count / len(tasks_with_deadline)
        avg_delay = total_delay_days / missed_count if missed_count > 0 else 0.0

        return DeadlineComplianceStatistics(
            total_tasks_with_deadline=len(tasks_with_deadline),
            met_deadline_count=met_count,
            missed_deadline_count=missed_count,
            compliance_rate=round(compliance_rate, 2),
            average_delay_days=round(avg_delay, 1),
        )

    def _calculate_priority_distribution(self, tasks: list[Task]) -> PriorityDistributionStatistics:
        """Calculate priority distribution statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            PriorityDistributionStatistics
        """
        high_count = 0
        medium_count = 0
        low_count = 0
        high_completed = 0
        high_total = 0

        # Map of priority -> completed count
        priority_map: dict[int, int] = defaultdict(int)

        for task in tasks:
            # Classify by priority level
            if task.priority >= self.HIGH_PRIORITY_THRESHOLD:
                high_count += 1
                high_total += 1
                if task.status == TaskStatus.COMPLETED:
                    high_completed += 1
            elif task.priority >= self.LOW_PRIORITY_THRESHOLD:
                medium_count += 1
            else:
                low_count += 1

            # Track completion by exact priority
            if task.status == TaskStatus.COMPLETED:
                priority_map[task.priority] += 1

        high_completion_rate = (high_completed / high_total) if high_total > 0 else 0.0

        return PriorityDistributionStatistics(
            high_priority_count=high_count,
            medium_priority_count=medium_count,
            low_priority_count=low_count,
            high_priority_completion_rate=round(high_completion_rate, 2),
            priority_completion_map=dict(priority_map),
        )

    def _calculate_trends(self, tasks: list[Task]) -> TrendStatistics:
        """Calculate trend statistics over time.

        Args:
            tasks: List of tasks to analyze

        Returns:
            TrendStatistics
        """
        now = datetime.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        last_7_completed = 0
        last_30_completed = 0

        # Weekly and monthly trends
        weekly_trend: dict[str, int] = defaultdict(int)
        monthly_trend: dict[str, int] = defaultdict(int)

        for task in tasks:
            if task.actual_end and task.is_finished:
                end_dt = datetime.strptime(task.actual_end, DATETIME_FORMAT)

                # Count for last N days
                if end_dt >= last_7_days:
                    last_7_completed += 1
                if end_dt >= last_30_days:
                    last_30_completed += 1

                # Weekly trend (ISO week)
                week_start = end_dt - timedelta(days=end_dt.weekday())
                week_key = week_start.strftime("%Y-W%U")
                weekly_trend[week_key] += 1

                # Monthly trend
                month_key = end_dt.strftime("%Y-%m")
                monthly_trend[month_key] += 1

        return TrendStatistics(
            last_7_days_completed=last_7_completed,
            last_30_days_completed=last_30_completed,
            weekly_completion_trend=dict(weekly_trend),
            monthly_completion_trend=dict(monthly_trend),
        )
