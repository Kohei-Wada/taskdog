"""Filter for today's tasks."""

from datetime import datetime

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.task_repository import TaskRepository
from shared.utils.date_utils import DateTimeParser


class TodayFilter:
    """Filter tasks relevant for today.

    Identifies tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS

    Also includes ancestor tasks to preserve hierarchy.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize filter with repository.

        Args:
            repository: Task repository for accessing task relationships
        """
        self.repository = repository

    def filter(self, tasks: list[Task], include_completed: bool = False) -> list[Task]:
        """Filter tasks that are relevant for today.

        Args:
            tasks: List of all tasks
            include_completed: Whether to include completed tasks

        Returns:
            List of tasks matching today's criteria
        """
        today = datetime.now().date()

        # First, identify tasks matching today's criteria
        matching_task_ids = set()

        for task in tasks:
            # Always skip archived tasks
            if task.status == TaskStatus.ARCHIVED:
                continue

            # Skip completed tasks unless include_completed is True
            if not include_completed and task.status == TaskStatus.COMPLETED:
                continue

            # Check if task matches today's criteria
            if self._is_today_task(task, today):
                matching_task_ids.add(task.id)

        # Include ancestor tasks to preserve hierarchy
        ancestor_ids = set()
        for task in tasks:
            if task.id in matching_task_ids:
                # Add all ancestors
                current = task
                while current.parent_id:
                    ancestor_ids.add(current.parent_id)
                    current = self.repository.get_by_id(current.parent_id)
                    if not current:
                        break

        # Combine matching tasks and their ancestors
        included_ids = matching_task_ids | ancestor_ids
        return [t for t in tasks if t.id in included_ids]

    def _is_today_task(self, task: Task, today) -> bool:
        """Check if a task is relevant for today.

        Args:
            task: Task to check
            today: Today's date (datetime.date object)

        Returns:
            True if task meets any of today's criteria
        """
        # Criterion A: Deadline is today
        if task.deadline:
            deadline_date = DateTimeParser.parse_date(task.deadline)
            if deadline_date == today:
                return True

        # Criterion B: Planned period includes today
        if task.planned_start and task.planned_end:
            planned_start_date = DateTimeParser.parse_date(task.planned_start)
            planned_end_date = DateTimeParser.parse_date(task.planned_end)
            if planned_start_date <= today <= planned_end_date:
                return True

        # Criterion C: Status is IN_PROGRESS
        return task.status == TaskStatus.IN_PROGRESS
