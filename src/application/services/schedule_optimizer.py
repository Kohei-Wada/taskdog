"""Schedule optimizer service for automatic task scheduling."""

import copy
from datetime import datetime, timedelta

from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task, TaskStatus


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
        self.daily_allocations: dict[str, float] = {}  # date_str -> hours

    def optimize_tasks(self, tasks: list[Task], repository) -> list[Task]:
        """Optimize schedules for all tasks.

        Args:
            tasks: List of tasks to optimize
            repository: Task repository for hierarchy queries

        Returns:
            List of tasks with updated schedules
        """
        # Filter tasks that need scheduling
        schedulable_tasks = self._get_schedulable_tasks(tasks)

        # Sort by priority
        sorted_tasks = self._sort_by_priority(schedulable_tasks, repository)

        # Allocate time blocks for each task
        updated_tasks = []
        for task in sorted_tasks:
            if self._should_schedule_task(task):
                updated_task = self._allocate_timeblock(task)
                if updated_task:
                    updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = self._update_parent_periods(tasks, updated_tasks, repository)

        return all_tasks_with_updates

    def _get_schedulable_tasks(self, tasks: list[Task]) -> list[Task]:
        """Get tasks that can be scheduled.

        Filters out completed tasks and optionally tasks with existing schedules.

        Args:
            tasks: All tasks

        Returns:
            List of schedulable tasks
        """
        schedulable = []
        for task in tasks:
            # Skip completed tasks
            if task.status == TaskStatus.COMPLETED:
                continue

            # Skip tasks without estimated duration
            if not task.estimated_duration:
                continue

            # Skip tasks with existing schedule unless force_override
            if task.planned_start and not self.force_override:
                continue

            schedulable.append(task)

        return schedulable

    def _sort_by_priority(self, tasks: list[Task], repository) -> list[Task]:
        """Sort tasks by scheduling priority.

        Priority order:
        1. Deadline urgency (closer deadline = higher priority)
        2. Task priority field
        3. Leaf tasks before parents (schedule children first)
        4. Task ID (for stable sort)

        Args:
            tasks: Tasks to sort
            repository: Task repository for hierarchy queries

        Returns:
            Sorted task list
        """

        def priority_key(task: Task) -> tuple:
            # Check if task is a parent (has children)
            children = repository.get_children(task.id)
            is_parent = len(children) > 0

            # Deadline score: None = infinity, otherwise days until deadline
            if task.deadline:
                deadline_dt = datetime.strptime(task.deadline, DATETIME_FORMAT)
                days_until = (deadline_dt - self.start_date).days
            else:
                days_until = float("inf")

            # Return tuple for sorting: (deadline, -priority, is_parent, id)
            # Higher priority value means higher priority (200 > 100 > 50)
            # Negative priority so higher values come first
            return (days_until, -task.priority, is_parent, task.id)

        return sorted(tasks, key=priority_key)

    def _should_schedule_task(self, task: Task) -> bool:
        """Check if task should be scheduled.

        Args:
            task: Task to check

        Returns:
            True if task should be scheduled
        """
        # Must have estimated duration
        if not task.estimated_duration:
            return False

        # If force_override is False, skip tasks with existing schedules
        if not self.force_override and task.planned_start:
            return False

        return True

    def _allocate_timeblock(self, task: Task) -> Task | None:
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

        # Set planned times (default to 18:00:00 for consistency with DateTimeWithDefault)
        if start_date and end_date:
            task_copy.planned_start = start_date.strftime(DATETIME_FORMAT)
            # End date should be end of work day
            task_copy.planned_end = end_date.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        return None

    def _update_parent_periods(
        self, all_tasks: list[Task], updated_tasks: list[Task], repository
    ) -> list[Task]:
        """Update parent task periods to encompass their children.

        Args:
            all_tasks: All tasks in the system
            updated_tasks: Tasks that were updated with new schedules
            repository: Task repository for hierarchy queries

        Returns:
            All tasks that were modified (updated tasks + affected parents)
        """
        modified_tasks = list(updated_tasks)
        task_map = {t.id: t for t in all_tasks}
        # Create map of updated tasks for easy lookup
        updated_task_map = {t.id: t for t in updated_tasks}

        # Collect all parent IDs that need updating
        parent_ids_to_update = set()
        for task in updated_tasks:
            if task.parent_id:
                parent_ids_to_update.add(task.parent_id)

        # Update each parent
        while parent_ids_to_update:
            parent_id = parent_ids_to_update.pop()
            parent_task = task_map.get(parent_id)

            if not parent_task:
                continue

            # Get all children from repository
            children_from_repo = repository.get_children(parent_id)
            if not children_from_repo:
                continue

            # Use updated versions of children if available
            children = []
            for child in children_from_repo:
                if child.id in updated_task_map:
                    children.append(updated_task_map[child.id])
                else:
                    children.append(child)

            # Find earliest start and latest end among children with schedules
            child_starts = [
                datetime.strptime(c.planned_start, DATETIME_FORMAT)
                for c in children
                if c.planned_start
            ]
            child_ends = [
                datetime.strptime(c.planned_end, DATETIME_FORMAT) for c in children if c.planned_end
            ]

            if child_starts and child_ends:
                parent_start = min(child_starts).strftime(DATETIME_FORMAT)
                parent_end = max(child_ends).strftime(DATETIME_FORMAT)

                # Update parent if period changed
                if (
                    parent_task.planned_start != parent_start
                    or parent_task.planned_end != parent_end
                ):
                    # Create a copy of parent task
                    parent_task_copy = copy.deepcopy(parent_task)
                    parent_task_copy.planned_start = parent_start
                    parent_task_copy.planned_end = parent_end

                    # Add to modified list
                    modified_tasks.append(parent_task_copy)
                    # Update the map so nested parents can use this updated version
                    updated_task_map[parent_task_copy.id] = parent_task_copy

                    # If this parent has a parent, update it too
                    if parent_task_copy.parent_id:
                        parent_ids_to_update.add(parent_task_copy.parent_id)

        return modified_tasks
