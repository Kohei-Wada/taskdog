"""Domain service for checking task eligibility for various operations.

This service centralizes the business rules for determining whether a task
should be included in various operations like scheduling, workload calculation,
and hierarchy updates.
"""

from domain.entities.task import Task, TaskStatus


class TaskEligibilityChecker:
    """Checks task eligibility for various operations based on business rules."""

    @staticmethod
    def is_schedulable(task: Task, force_override: bool = False) -> bool:
        """Check if task can be scheduled.

        Args:
            task: The task to check
            force_override: Whether to allow rescheduling of already-scheduled tasks

        Returns:
            True if task can be scheduled

        Business Rules:
            - Must have estimated_duration set
            - Must be PENDING status (not IN_PROGRESS, COMPLETED, FAILED, or ARCHIVED)
            - If force_override is False, must not have existing schedule
        """
        # Skip completed and archived tasks
        if task.status in (TaskStatus.COMPLETED, TaskStatus.ARCHIVED):
            return False

        # Skip IN_PROGRESS tasks (don't reschedule tasks already being worked on)
        if task.status == TaskStatus.IN_PROGRESS:
            return False

        # Skip tasks without estimated duration
        if not task.estimated_duration:
            return False

        # Skip tasks with existing schedule unless force_override
        return not (task.planned_start and not force_override)

    @staticmethod
    def should_count_in_workload(task: Task) -> bool:
        """Check if task should be counted in workload calculations.

        Args:
            task: The task to check

        Returns:
            True if task should be included in workload

        Business Rules:
            - Exclude COMPLETED tasks (work already done)
            - Exclude ARCHIVED tasks (historical records)
            - Include PENDING and IN_PROGRESS tasks
        """
        return not task.is_finished

    @staticmethod
    def can_be_rescheduled(task: Task) -> bool:
        """Check if task can be rescheduled (used in force_override mode).

        Args:
            task: The task to check

        Returns:
            True if task can have its schedule overridden

        Business Rules:
            - Exclude COMPLETED tasks (finalized)
            - Exclude ARCHIVED tasks (historical)
            - Exclude IN_PROGRESS tasks (currently being worked on)
            - Include only PENDING tasks
        """
        return task.status == TaskStatus.PENDING

    @staticmethod
    def can_be_updated_in_hierarchy(task: Task) -> bool:
        """Check if task can be updated as part of hierarchy operations.

        Args:
            task: The task to check

        Returns:
            True if task can be updated in hierarchy operations

        Business Rules:
            - Exclude ARCHIVED tasks (they are historical records and should not change)
            - Include all other statuses
        """
        return task.can_be_modified
