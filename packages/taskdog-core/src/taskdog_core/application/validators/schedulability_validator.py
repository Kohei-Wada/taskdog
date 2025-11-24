"""Validator for task schedulability during optimization."""

from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.exceptions.task_exceptions import (
    NoSchedulableTasksError,
    TaskNotFoundException,
    TaskNotSchedulableError,
)


class SchedulabilityValidator:
    """Validator for task schedulability constraints.

    Business Rules:
    - Tasks must exist in the repository
    - Tasks must not be archived
    - Tasks must not be finished (COMPLETED or CANCELED)
    - Tasks must not be in progress
    - Tasks must have estimated_duration set
    - Tasks must not be fixed
    - If not force_override, tasks must not have existing schedules
    """

    @staticmethod
    def validate_and_filter_schedulable_tasks(
        task_ids: list[int],
        all_tasks: list[Task],
        force_override: bool,
    ) -> list[Task]:
        """Validate task IDs and return schedulable tasks.

        Args:
            task_ids: List of task IDs to validate
            all_tasks: All tasks from repository
            force_override: Whether to allow overriding existing schedules

        Returns:
            List of schedulable tasks

        Raises:
            TaskNotFoundException: If any task_id doesn't exist
            NoSchedulableTasksError: If no tasks are schedulable
        """
        # Build task ID map for efficient lookup
        task_map = {t.id: t for t in all_tasks if t.id is not None}

        # Validate that all requested task IDs exist
        missing_ids = [tid for tid in task_ids if tid not in task_map]
        if missing_ids:
            if len(missing_ids) == 1:
                raise TaskNotFoundException(missing_ids[0])
            raise TaskNotFoundException(
                f"Tasks with IDs {', '.join(map(str, missing_ids))} not found"
            )

        # Get the requested tasks
        requested_tasks = [task_map[tid] for tid in task_ids]

        # Validate each task's schedulability and collect reasons for failures
        schedulable_tasks = []
        reasons: dict[int, str] = {}

        for task in requested_tasks:
            try:
                # Delegate validation to entity (domain logic)
                task.validate_schedulable(force_override)
                schedulable_tasks.append(task)
            except TaskNotSchedulableError as e:
                # Collect failure reason from exception
                reasons[e.task_id] = e.reason

        # If no tasks are schedulable, raise error with detailed reasons
        if not schedulable_tasks:
            raise NoSchedulableTasksError(task_ids=task_ids, reasons=reasons)

        return schedulable_tasks
