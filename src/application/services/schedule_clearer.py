"""Service for clearing task schedules."""

from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class ScheduleClearer:
    """Service for clearing schedule-related fields from tasks.

    This service handles the responsibility of clearing schedule data
    (planned_start, planned_end, daily_allocations) from tasks.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize service.

        Args:
            repository: Task repository for data persistence
        """
        self.repository = repository

    def clear_schedules(self, tasks: list[Task]) -> list[Task]:
        """Clear schedule fields from given tasks and persist changes.

        Clears planned_start, planned_end, and daily_allocations for each task.

        Args:
            tasks: List of tasks to clear schedules from

        Returns:
            List of tasks with cleared schedules
        """
        for task in tasks:
            task.planned_start = None
            task.planned_end = None
            task.daily_allocations = {}
            self.repository.save(task)

        return tasks
