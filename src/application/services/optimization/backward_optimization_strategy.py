"""Backward optimization strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.hierarchy_manager import HierarchyManager
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task


class BackwardOptimizationStrategy(OptimizationStrategy):
    """Backward (Just-In-Time) algorithm for task scheduling optimization.

    This strategy schedules tasks as late as possible while meeting deadlines:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Sort tasks by deadline (furthest deadline first)
    3. For each task, allocate time blocks backward from deadline
    4. Fill time slots from deadline backwards
    5. Update parent task periods based on children

    Benefits:
    - Maximum flexibility for requirement changes
    - Prevents early resource commitment
    - Just-In-Time delivery approach
    - Keeps options open longer
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using backward algorithm.

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
        hierarchy_manager = HierarchyManager(repository)

        # Initialize daily_allocations with existing scheduled tasks
        allocator.initialize_allocations(tasks, force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # Sort by deadline (furthest first) for backward allocation
        sorted_tasks = self._sort_by_deadline_desc(schedulable_tasks, start_date)

        # Allocate time blocks for each task backward from deadline
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_backward_timeblock(
                task, allocator, start_date, max_hours_per_day
            )
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = hierarchy_manager.update_parent_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if force_override:
            all_tasks_with_updates = hierarchy_manager.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        # Return modified tasks and daily allocations
        return all_tasks_with_updates, allocator.daily_allocations

    def _sort_by_deadline_desc(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by deadline (furthest first).

        Tasks without deadlines are placed at the beginning
        (they will be scheduled first = furthest from now).

        Args:
            tasks: Tasks to sort
            start_date: Reference date for deadline calculation

        Returns:
            Sorted task list (furthest deadline first)
        """

        def deadline_key(task: Task) -> tuple:
            if task.deadline:
                deadline_dt = datetime.strptime(task.deadline, DATETIME_FORMAT)
                days_until = (deadline_dt - start_date).days
                # Negative to get furthest first
                return (0, -days_until, task.id)
            else:
                # Tasks without deadline: schedule first (no deadline pressure)
                return (1, 0, task.id)

        return sorted(tasks, key=deadline_key)

    def _allocate_backward_timeblock(
        self,
        task: Task,
        allocator: WorkloadAllocator,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block backward from deadline.

        Args:
            task: Task to schedule
            allocator: Workload allocator (for tracking daily_allocations)
            start_date: Earliest allowed start date
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

        # Determine the target end date
        if task_copy.deadline:
            target_end = datetime.strptime(task_copy.deadline, DATETIME_FORMAT)
        else:
            # If no deadline, schedule in near future (e.g., 1 week from start)
            target_end = start_date + timedelta(days=7)

        # Allocate backward from target_end
        current_date = target_end
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations = {}

        # Collect allocations in reverse order
        temp_allocations = []

        while remaining_hours > 0:
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date -= timedelta(days=1)
                continue

            # Don't go before start_date
            if current_date < start_date:
                # Cannot schedule - insufficient time before deadline
                return None

            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = allocator.daily_allocations.get(date_str, 0.0)

            # Calculate available hours for this day
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                # Allocate as much as possible for this day
                allocated = min(remaining_hours, available_hours)
                temp_allocations.append((date_str, allocated, current_date))
                remaining_hours -= allocated

            current_date -= timedelta(days=1)

        # Apply allocations (we collected them in reverse, so apply in correct order)
        for date_str, hours, date_obj in reversed(temp_allocations):
            allocator.daily_allocations[date_str] = (
                allocator.daily_allocations.get(date_str, 0.0) + hours
            )
            task_daily_allocations[date_str] = hours

            # Track start and end
            if schedule_start is None:
                schedule_start = date_obj
            schedule_end = date_obj

        # Set planned times
        if schedule_start and schedule_end:
            # Use start_date's time for schedule_start
            start_with_time = schedule_start.replace(
                hour=start_date.hour, minute=start_date.minute, second=start_date.second
            )
            task_copy.planned_start = start_with_time.strftime(DATETIME_FORMAT)

            # Use DEFAULT_END_HOUR for schedule_end
            end_date_with_time = schedule_end.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        return None
