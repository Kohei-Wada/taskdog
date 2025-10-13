"""Round-robin optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.hierarchy_manager import HierarchyManager
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR, DEFAULT_START_HOUR
from domain.entities.task import Task


class RoundRobinOptimizationStrategy(OptimizationStrategy):
    """Round-robin algorithm for task scheduling optimization.

    This strategy allocates time to tasks in a rotating manner:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Each day, distribute available hours equally among all active tasks
    3. Rotate through tasks until all are completed
    4. Ideal for parallel progress on multiple projects
    5. Update parent task periods based on children
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using round-robin algorithm.

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
        task_filter = TaskFilter()
        hierarchy_manager = HierarchyManager(repository)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        if not schedulable_tasks:
            return [], {}

        # Filter out tasks without ID (should not happen, but for type safety)
        schedulable_tasks = [t for t in schedulable_tasks if t.id is not None]

        # Track remaining hours for each task
        task_remaining: dict[int, float] = {
            task.id: task.estimated_duration or 0.0
            for task in schedulable_tasks
            if task.id is not None
        }
        task_map: dict[int, Task] = {
            task.id: copy.deepcopy(task) for task in schedulable_tasks if task.id is not None
        }

        # Track allocations per task and per day
        task_daily_allocations: dict[int, dict[str, float]] = {
            task.id: {} for task in schedulable_tasks if task.id is not None
        }
        daily_allocations: dict[str, float] = {}

        # Track start and end dates for each task
        task_start_dates: dict[int, datetime] = {}
        task_end_dates: dict[int, datetime] = {}

        # Allocate time in round-robin fashion
        self._allocate_round_robin(
            task_remaining,
            task_daily_allocations,
            daily_allocations,
            task_start_dates,
            task_end_dates,
            start_date,
            max_hours_per_day,
        )

        # Build updated tasks with schedules
        updated_tasks = self._build_updated_tasks(
            task_map, task_start_dates, task_end_dates, task_daily_allocations
        )

        # Update parent task periods based on children
        all_tasks_with_updates = hierarchy_manager.update_parent_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if force_override:
            all_tasks_with_updates = hierarchy_manager.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        # Return modified tasks and daily allocations
        return all_tasks_with_updates, daily_allocations

    def _allocate_round_robin(
        self,
        task_remaining: dict[int, float],
        task_daily_allocations: dict[int, dict[str, float]],
        daily_allocations: dict[str, float],
        task_start_dates: dict[int, datetime],
        task_end_dates: dict[int, datetime],
        start_date: datetime,
        max_hours_per_day: float,
    ) -> None:
        """Allocate time in round-robin fashion across tasks.

        Args:
            task_remaining: Dict of remaining hours per task
            task_daily_allocations: Dict of daily allocations per task
            daily_allocations: Dict of total daily allocations
            task_start_dates: Dict to store task start dates
            task_end_dates: Dict to store task end dates
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day
        """
        current_date = start_date
        max_iterations = 10000  # Safety limit to prevent infinite loops

        iteration = 0
        while any(hours > 0.001 for hours in task_remaining.values()):
            iteration += 1
            if iteration > max_iterations:
                break

            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
                continue

            date_str = current_date.strftime("%Y-%m-%d")

            # Get active tasks (with remaining hours)
            active_tasks = [tid for tid, remaining in task_remaining.items() if remaining > 0.001]

            if not active_tasks:
                break

            # Distribute available hours equally among active tasks
            hours_per_task = max_hours_per_day / len(active_tasks)

            daily_total = 0.0
            for task_id in active_tasks:
                # Allocate up to hours_per_task, but not more than remaining
                allocated = min(hours_per_task, task_remaining[task_id])
                task_remaining[task_id] -= allocated

                # Record allocation
                task_daily_allocations[task_id][date_str] = allocated
                daily_total += allocated

                # Track start and end dates
                if task_id not in task_start_dates:
                    task_start_dates[task_id] = current_date
                task_end_dates[task_id] = current_date

            daily_allocations[date_str] = daily_total

            # Move to next day
            current_date += timedelta(days=1)

    def _build_updated_tasks(
        self,
        task_map: dict[int, Task],
        task_start_dates: dict[int, datetime],
        task_end_dates: dict[int, datetime],
        task_daily_allocations: dict[int, dict[str, float]],
    ) -> list[Task]:
        """Build updated tasks with schedules.

        Args:
            task_map: Dict of tasks by ID
            task_start_dates: Dict of task start dates
            task_end_dates: Dict of task end dates
            task_daily_allocations: Dict of daily allocations per task

        Returns:
            List of updated tasks with schedules
        """
        updated_tasks = []
        for task_id, task in task_map.items():
            if task_id in task_start_dates:
                start_dt = task_start_dates[task_id]
                end_dt = task_end_dates[task_id]

                # Set start time to DEFAULT_START_HOUR (9:00)
                start_with_time = start_dt.replace(hour=DEFAULT_START_HOUR, minute=0, second=0)
                # Set end time to DEFAULT_END_HOUR (18:00)
                end_with_time = end_dt.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)

                task.planned_start = start_with_time.strftime(DATETIME_FORMAT)
                task.planned_end = end_with_time.strftime(DATETIME_FORMAT)
                task.daily_allocations = task_daily_allocations[task_id]

                updated_tasks.append(task)

        return updated_tasks
