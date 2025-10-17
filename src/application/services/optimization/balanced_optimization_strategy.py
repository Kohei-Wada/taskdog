"""Balanced optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator


class BalancedOptimizationStrategy(OptimizationStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. For each task, distribute hours evenly from start_date to deadline
    3. Respect max_hours_per_day constraint and weekday-only rule

    Benefits:
    - More realistic workload distribution
    - Prevents burnout by avoiding front-heavy scheduling
    - Better work-life balance

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by priority (balanced approach).

        Uses OptimizationTaskSorter which considers:
        - Deadline urgency (closer deadline = higher priority)
        - Priority field value
        - Task ID (for stable sorting)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by priority (highest priority first)
        """
        sorter = OptimizationTaskSorter(start_date, repository)
        return sorter.sort_by_priority(tasks)

    def _allocate_task(  # noqa: C901
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block with balanced distribution.

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        if not task.estimated_duration:
            return None

        # Create a deep copy to avoid modifying the original task
        task_copy = copy.deepcopy(task)

        # Type narrowing: estimated_duration is guaranteed to be float at this point
        assert task_copy.estimated_duration is not None

        # Calculate effective deadline considering parent task deadlines
        effective_deadline = DeadlineCalculator.get_effective_deadline(task_copy, self.repository)

        # Calculate end date for distribution
        if effective_deadline:
            end_date = datetime.strptime(effective_deadline, DATETIME_FORMAT)
        else:
            # If no deadline, use a reasonable period (2 weeks = 10 weekdays)
            # 13 days from start gives us 2 weeks of weekdays
            end_date = start_date + timedelta(days=13)

        # Calculate available weekdays in the period
        available_weekdays = self._count_weekdays(start_date, end_date)

        if available_weekdays == 0:
            return None

        # Calculate target hours per day (even distribution)
        target_hours_per_day = task_copy.estimated_duration / available_weekdays

        # Try to allocate with balanced distribution
        current_date = start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations = {}

        while remaining_hours > 0 and current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
                continue

            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = self.daily_allocations.get(date_str, 0.0)

            # Calculate how much we want to allocate today (balanced approach)
            desired_allocation = min(target_hours_per_day, remaining_hours)

            # Check available hours considering max_hours_per_day constraint
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                # Record start date on first allocation
                if schedule_start is None:
                    schedule_start = current_date

                # Allocate as much as possible (up to desired amount)
                allocated = min(desired_allocation, available_hours)
                self.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Check if we couldn't allocate all hours
        if remaining_hours > 0:
            # Rollback allocations and return None
            for date_str, hours in task_daily_allocations.items():
                self.daily_allocations[date_str] -= hours
            return None

        # Set planned times
        if schedule_start and schedule_end:
            task_copy.planned_start = schedule_start.strftime(DATETIME_FORMAT)
            end_date_with_time = schedule_end.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        return None

    def _count_weekdays(self, start_date: datetime, end_date: datetime) -> int:
        """Count weekdays between start and end date (inclusive).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of weekdays
        """
        count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Monday=0 to Friday=4
                count += 1
            current += timedelta(days=1)
        return count
