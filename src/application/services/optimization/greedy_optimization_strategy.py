"""Greedy optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.
    """

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by priority (greedy approach).

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

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocation.

        Finds the earliest available time slot that satisfies:
        - Starts on or after start_date
        - Respects max_hours_per_day constraint
        - Allocates across weekdays only
        - Fills each day greedily (maximum possible hours per day)

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

        # Save original state to revert if allocation fails
        original_daily_allocations = copy.deepcopy(self.daily_allocations)

        # Calculate effective deadline considering parent task deadlines
        effective_deadline = DeadlineCalculator.get_effective_deadline(task_copy, self.repository)

        # Find earliest available start date
        current_date = start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None

        # Track first allocation day
        first_allocation = True

        # Track this task's daily allocations
        task_daily_allocations = {}

        while remaining_hours > 0:
            # Skip weekends
            if self._is_weekend(current_date):
                current_date += timedelta(days=1)
                continue

            # Check deadline constraint using effective deadline
            if effective_deadline:
                deadline_dt = datetime.strptime(effective_deadline, DATETIME_FORMAT)
                if current_date > deadline_dt:
                    # Cannot schedule before deadline - revert allocations
                    self.daily_allocations = original_daily_allocations
                    return None

            # Get current allocation for this day
            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = self.daily_allocations.get(date_str, 0.0)

            # Calculate available hours for this day
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                # Record start date on first allocation
                if first_allocation:
                    schedule_start = current_date
                    first_allocation = False

                # Allocate as much as possible for this day (greedy approach)
                allocated = min(remaining_hours, available_hours)
                self.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Set planned times with appropriate default hours
        if schedule_start and schedule_end:
            # Start date keeps its time (from start_date, typically 9:00)
            task_copy.planned_start = schedule_start.strftime(DATETIME_FORMAT)
            # End date should be end of work day (18:00)
            end_date_with_time = schedule_end.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        # Failed to allocate - revert allocations
        self.daily_allocations = original_daily_allocations
        return None
