"""Validator for estimated_duration field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task
from domain.exceptions.task_exceptions import CannotSetEstimateForParentTaskError
from infrastructure.persistence.task_repository import TaskRepository


class EstimatedDurationValidator(FieldValidator):
    """Validator for estimated_duration field updates.

    Business Rules:
    - Cannot set estimated_duration for parent tasks (tasks with children)
    - Parent task's estimated_duration is auto-calculated from children
    """

    def validate(self, value: float, task: Task, repository: TaskRepository) -> None:
        """Validate estimated_duration update.

        Args:
            value: New estimated_duration (float, hours)
            task: Task being updated
            repository: Repository for data access

        Raises:
            CannotSetEstimateForParentTaskError: If task has children
        """
        # Ensure task has ID (from repository)
        assert task.id is not None

        # Check if task has children
        children = repository.get_children(task.id)
        if children:
            raise CannotSetEstimateForParentTaskError(task.id, len(children))
