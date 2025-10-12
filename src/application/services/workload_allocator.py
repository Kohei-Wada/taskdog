"""Workload allocator service for task time block allocation."""

import copy
from datetime import datetime, timedelta

from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR
from domain.entities.task import Task, TaskStatus


class WorkloadAllocator:
    """Service for allocating time blocks to tasks.

    Manages daily work hour allocations and assigns time blocks to tasks
    while respecting workload constraints (weekdays only, max hours per day).
    """

    def __init__(self, max_hours_per_day: float, start_date: datetime):
        """Initialize allocator.

        Args:
            max_hours_per_day: Maximum work hours per day
            start_date: Starting date for allocations
        """
        self.max_hours_per_day = max_hours_per_day
        self.start_date = start_date
        self.daily_allocations: dict[str, float] = {}  # date_str -> hours

    def initialize_allocations(self, tasks: list[Task], force_override: bool):
        """Initialize daily_allocations with existing scheduled tasks.

        This method pre-populates daily_allocations with hours from tasks
        that already have schedules. This ensures that when we optimize new tasks,
        we account for existing workload commitments.

        Args:
            tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden
        """
        # Build parent-child map to identify parent tasks
        parent_ids = set()
        for task in tasks:
            if task.parent_id:
                parent_ids.add(task.parent_id)

        for task in tasks:
            # Skip parent tasks (they don't have actual work, only children do)
            if task.id in parent_ids:
                continue

            # Skip completed tasks
            if task.status == TaskStatus.COMPLETED:
                continue

            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # If force_override, we'll reschedule PENDING tasks, so don't count their old allocation
            # But IN_PROGRESS tasks should NOT be rescheduled, so count their allocation
            if force_override and task.status != TaskStatus.IN_PROGRESS:
                continue

            # Use daily_allocations if available
            if task.daily_allocations:
                for date_str, hours in task.daily_allocations.items():
                    if date_str in self.daily_allocations:
                        self.daily_allocations[date_str] += hours
                    else:
                        self.daily_allocations[date_str] = hours

    def allocate_timeblock(self, task: Task) -> Task | None:
        """Allocate time block for a task.

        Finds the earliest available time slot that satisfies:
        - Starts on or after self.start_date
        - Respects max_hours_per_day constraint
        - Allocates across weekdays only

        Args:
            task: Task to schedule

        Returns:
            Copy of task with updated planned_start/end and daily_allocations, or None if allocation fails
        """
        if not task.estimated_duration:
            return None

        # Create a deep copy to avoid modifying the original task
        task_copy = copy.deepcopy(task)

        # Find earliest available start date
        current_date = self.start_date
        remaining_hours = task_copy.estimated_duration
        start_date = None
        end_date = None

        # Track first allocation day
        first_allocation = True

        # Track this task's daily allocations
        task_daily_allocations = {}

        while remaining_hours > 0:
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
                continue

            # Check deadline constraint
            if task_copy.deadline:
                deadline_dt = datetime.strptime(task_copy.deadline, DATETIME_FORMAT)
                if current_date > deadline_dt:
                    # Cannot schedule before deadline
                    return None

            # Get current allocation for this day
            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = self.daily_allocations.get(date_str, 0.0)

            # Calculate available hours for this day
            available_hours = self.max_hours_per_day - current_allocation

            if available_hours > 0:
                # Record start date on first allocation
                if first_allocation:
                    start_date = current_date
                    first_allocation = False

                # Allocate as much as possible for this day
                allocated = min(remaining_hours, available_hours)
                self.daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                end_date = current_date

            current_date += timedelta(days=1)

        # Set planned times with appropriate default hours
        if start_date and end_date:
            # Start date keeps its time (from self.start_date, typically 9:00)
            task_copy.planned_start = start_date.strftime(DATETIME_FORMAT)
            # End date should be end of work day (18:00)
            end_date_with_time = end_date.replace(hour=DEFAULT_END_HOUR, minute=0, second=0)
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        return None
