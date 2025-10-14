"""Task filter service for scheduling."""

from domain.entities.task import Task
from domain.services.task_eligibility_checker import TaskEligibilityChecker


class TaskFilter:
    """Service for filtering tasks based on scheduling criteria.

    Determines which tasks should be considered for scheduling
    based on their status, estimated duration, and existing schedules.
    """

    def get_schedulable_tasks(self, tasks: list[Task], force_override: bool) -> list[Task]:
        """Get tasks that can be scheduled.

        Filters out completed tasks and optionally tasks with existing schedules.

        Args:
            tasks: All tasks
            force_override: Whether to include tasks with existing schedules

        Returns:
            List of schedulable tasks
        """
        schedulable = []
        for task in tasks:
            if self.should_schedule_task(task, force_override):
                schedulable.append(task)

        return schedulable

    def should_schedule_task(self, task: Task, force_override: bool) -> bool:
        """Check if task should be scheduled.

        Args:
            task: Task to check
            force_override: Whether to override existing schedules

        Returns:
            True if task should be scheduled
        """
        return TaskEligibilityChecker.is_schedulable(task, force_override)
