"""Use case for removing a task."""

from application.use_cases.base import UseCase
from application.dto.remove_task_input import RemoveTaskInput
from infrastructure.persistence.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[RemoveTaskInput, int]):
    """Use case for removing tasks.

    Supports two removal modes:
    - Orphan mode (default): Removes task and sets children's parent_id to None
    - Cascade mode: Recursively removes task and all its descendants

    Returns the number of tasks removed.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: RemoveTaskInput) -> int:
        """Execute task removal.

        Args:
            input_dto: Task removal input data

        Returns:
            Number of tasks removed

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        self._get_task_or_raise(self.repository, input_dto.task_id)

        if input_dto.cascade:
            return self._remove_cascade(input_dto.task_id)
        else:
            return self._remove_orphan(input_dto.task_id)

    def _remove_cascade(self, task_id: int) -> int:
        """Recursively remove task and all its children.

        Args:
            task_id: ID of the task to remove

        Returns:
            Number of tasks removed
        """
        removed_count = 0

        # Recursively remove all children first
        children = self.repository.get_children(task_id)
        for child in children:
            removed_count += self._remove_cascade(child.id)

        # Remove the task itself
        self.repository.delete(task_id)
        removed_count += 1

        return removed_count

    def _remove_orphan(self, task_id: int) -> int:
        """Remove task and orphan its children.

        Args:
            task_id: ID of the task to remove

        Returns:
            Number of tasks removed (always 1)
        """
        # Orphan children (set their parent_id to None)
        children = self.repository.get_children(task_id)
        for child in children:
            child.parent_id = None
            self.repository.save(child)

        # Remove the task itself
        self.repository.delete(task_id)
        return 1
