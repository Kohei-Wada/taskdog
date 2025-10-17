"""Dependency-aware optimization strategy implementation using Critical Path Method."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator


class DependencyAwareOptimizationStrategy(OptimizationStrategy):
    """Dependency-aware algorithm using Critical Path Method (CPM).

    This strategy schedules tasks while respecting parent-child dependencies:
    1. Calculate dependency depth for each task (children are scheduled before parents)
    2. Sort by dependency depth (leaf tasks first, then their parents)
    3. Within same depth, use priority and deadline as secondary sort
    4. Allocate time blocks respecting the dependency order using greedy allocation

    The allocation uses greedy forward allocation, filling each day to maximum
    capacity before moving to the next day.
    """

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by dependency depth, then by priority/deadline.

        Calculate dependency depth for each task and sort with multiple criteria:
        - Primary: Dependency depth (lower depth = scheduled first)
        - Secondary: Deadline (earlier deadline = scheduled first)
        - Tertiary: Priority (higher priority = scheduled first)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by dependency depth, deadline, and priority
        """
        # Calculate dependency depth for each task
        task_depths = self._calculate_dependency_depths(tasks, repository)

        # Sort by dependency depth (leaf tasks first), then by priority/deadline
        return sorted(
            tasks,
            key=lambda t: (
                task_depths.get(
                    t.id if t.id is not None else 0, 0
                ),  # Lower depth = scheduled first
                # Secondary sort: deadline urgency
                (t.deadline if t.deadline else "9999-12-31 23:59:59"),
                # Tertiary sort: priority (higher = scheduled first, so negate)
                -(t.priority if t.priority is not None else 0),
            ),
        )

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocation.

        Finds the earliest available time slot and fills days greedily.

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        if not task.estimated_duration:
            return None

        task_copy = copy.deepcopy(task)

        # Type narrowing: estimated_duration is guaranteed to be float at this point
        assert task_copy.estimated_duration is not None

        original_daily_allocations = copy.deepcopy(self.daily_allocations)
        effective_deadline = DeadlineCalculator.get_effective_deadline(task_copy, self.repository)

        current_date = start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        first_allocation = True
        task_daily_allocations = {}

        while remaining_hours > 0:
            if self._is_weekend(current_date):
                current_date += timedelta(days=1)
                continue

            if effective_deadline:
                deadline_dt = datetime.strptime(effective_deadline, DATETIME_FORMAT)
                if current_date > deadline_dt:
                    self.daily_allocations = original_daily_allocations
                    return None

            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = self.daily_allocations.get(date_str, 0.0)
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                if first_allocation:
                    schedule_start = current_date
                    first_allocation = False

                allocated = min(remaining_hours, available_hours)
                self.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated
                schedule_end = current_date

            current_date += timedelta(days=1)

        if schedule_start and schedule_end:
            task_copy.planned_start = schedule_start.strftime(DATETIME_FORMAT)
            end_date_with_time = schedule_end.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        self.daily_allocations = original_daily_allocations
        return None

    def _calculate_dependency_depths(self, tasks: list[Task], repository) -> dict[int, int]:
        """Calculate dependency depth for each task.

        Since parent-child relationships have been removed, all tasks have depth 0.

        Args:
            tasks: List of tasks to analyze
            repository: Task repository (unused, kept for compatibility)

        Returns:
            Dict mapping task_id to dependency depth (always 0)
        """
        # All tasks have depth 0 now (no hierarchy)
        return {task.id: 0 for task in tasks if task.id is not None}
