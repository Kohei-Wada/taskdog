"""Balanced optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.schedule_propagator import SchedulePropagator
from application.services.task_filter import TaskFilter
from application.services.task_prioritizer import TaskPrioritizer
from application.services.workload_allocator import WorkloadAllocator
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task


class BalancedOptimizationStrategy(OptimizationStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Sort tasks by priority (deadline urgency, priority field, hierarchy)
    3. For each task, distribute hours evenly from start_date to deadline
    4. Respect max_hours_per_day constraint and weekday-only rule
    5. Update parent task periods based on children

    Benefits:
    - More realistic workload distribution
    - Prevents burnout by avoiding front-heavy scheduling
    - Better work-life balance
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using balanced algorithm.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Tuple of (modified_tasks, daily_allocations)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
        """
        # Initialize service instances
        allocator = WorkloadAllocator(max_hours_per_day, start_date)
        task_filter = TaskFilter()
        prioritizer = TaskPrioritizer(start_date, repository)
        schedule_propagator = SchedulePropagator(repository)

        # Initialize daily_allocations with existing scheduled tasks
        allocator.initialize_allocations(tasks, force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # Sort by priority
        sorted_tasks = prioritizer.sort_by_priority(schedulable_tasks)

        # Allocate time blocks for each task with balanced distribution
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_balanced_timeblock(
                task, allocator, start_date, max_hours_per_day
            )
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = schedule_propagator.propagate_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if force_override:
            all_tasks_with_updates = schedule_propagator.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        # Return modified tasks and daily allocations
        return all_tasks_with_updates, allocator.daily_allocations

    def _allocate_balanced_timeblock(  # noqa: C901
        self,
        task: Task,
        allocator: WorkloadAllocator,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block with balanced distribution.

        Args:
            task: Task to schedule
            allocator: Workload allocator (for tracking daily_allocations)
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

        # Calculate end date for distribution
        if task_copy.deadline:
            end_date = datetime.strptime(task_copy.deadline, DATETIME_FORMAT)
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
            current_allocation = allocator.daily_allocations.get(date_str, 0.0)

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
                allocator.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Check if we couldn't allocate all hours
        if remaining_hours > 0:
            # Rollback allocations and return None
            for date_str, hours in task_daily_allocations.items():
                allocator.daily_allocations[date_str] -= hours
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
