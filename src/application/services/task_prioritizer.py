"""Task prioritizer service for scheduling."""

from datetime import datetime

from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task


class TaskPrioritizer:
    """Service for sorting tasks by scheduling priority.

    Determines the optimal order for scheduling tasks based on
    deadline urgency, priority field, hierarchy, and task ID.
    """

    def __init__(self, start_date: datetime, repository):
        """Initialize prioritizer.

        Args:
            start_date: Starting date for deadline calculations
            repository: Task repository for hierarchy queries
        """
        self.start_date = start_date
        self.repository = repository

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by scheduling priority.

        Priority order:
        1. Deadline urgency (closer deadline = higher priority)
        2. Task priority field
        3. Leaf tasks before parents (schedule children first)
        4. Task ID (for stable sort)

        Args:
            tasks: Tasks to sort

        Returns:
            Sorted task list
        """

        def priority_key(task: Task) -> tuple:
            # Check if task is a parent (has children)
            children = self.repository.get_children(task.id)
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
