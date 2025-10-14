"""Task prioritizer service for scheduling."""

from datetime import datetime

from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator


class TaskPrioritizer:
    """Service for sorting tasks by scheduling priority.

    Determines the optimal order for scheduling tasks based on
    deadline urgency, priority field, and task ID.
    """

    def __init__(self, start_date: datetime, repository):
        """Initialize prioritizer.

        Args:
            start_date: Starting date for deadline calculations
            repository: Task repository (unused, kept for compatibility)
        """
        self.start_date = start_date
        self.repository = repository

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by scheduling priority.

        Priority order:
        1. Deadline urgency (closer deadline = higher priority)
        2. Task priority field
        3. Task ID (for stable sort)

        Args:
            tasks: Tasks to sort

        Returns:
            Sorted task list
        """

        def priority_key(task: Task) -> tuple:
            # Get task's deadline
            effective_deadline = DeadlineCalculator.get_effective_deadline(task, self.repository)

            # Deadline score: None = infinity, otherwise days until deadline
            if effective_deadline:
                deadline_dt = datetime.strptime(effective_deadline, DATETIME_FORMAT)
                days_until = (deadline_dt - self.start_date).days
            else:
                days_until = float("inf")

            # Handle priority=None (treat as 0)
            priority_value = task.priority if task.priority is not None else 0

            # Return tuple for sorting: (deadline, -priority, id)
            # Higher priority value means higher priority (200 > 100 > 50)
            # Negative priority so higher values come first
            return (days_until, -priority_value, task.id)

        return sorted(tasks, key=priority_key)
