"""Schedule optimizer service for automatic task scheduling."""

from datetime import datetime

from application.services.hierarchy_manager import HierarchyManager
from application.services.task_filter import TaskFilter
from application.services.task_prioritizer import TaskPrioritizer
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class ScheduleOptimizer:
    """Service for optimizing task schedules.

    Analyzes tasks and generates optimal planned_start/end dates based on:
    - Priority and deadlines
    - Estimated duration
    - Task hierarchy
    - Workload constraints (weekdays only, max hours per day)
    """

    def __init__(
        self, start_date: datetime, max_hours_per_day: float = 6.0, force_override: bool = False
    ):
        """Initialize optimizer.

        Args:
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day (default: 6.0)
            force_override: Whether to override existing schedules (default: False)
        """
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.force_override = force_override
        self.allocator = WorkloadAllocator(max_hours_per_day, start_date)
        self.filter = TaskFilter()

    def optimize_tasks(self, tasks: list[Task], repository) -> list[Task]:
        """Optimize schedules for all tasks.

        Args:
            tasks: List of tasks to optimize
            repository: Task repository for hierarchy queries

        Returns:
            List of tasks with updated schedules
        """
        # Initialize service instances
        prioritizer = TaskPrioritizer(self.start_date, repository)
        hierarchy_manager = HierarchyManager(repository)

        # Initialize daily_allocations with existing scheduled tasks
        # This ensures we account for tasks that won't be rescheduled
        self.allocator.initialize_allocations(tasks, self.force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = self.filter.get_schedulable_tasks(tasks, self.force_override)

        # Sort by priority
        sorted_tasks = prioritizer.sort_by_priority(schedulable_tasks)

        # Allocate time blocks for each task
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self.allocator.allocate_timeblock(task)
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = hierarchy_manager.update_parent_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if self.force_override:
            all_tasks_with_updates = hierarchy_manager.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        return all_tasks_with_updates
