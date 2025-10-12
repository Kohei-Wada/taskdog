"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.base import UseCase
from domain.entities.task import TaskStatus
from infrastructure.persistence.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskInput, int]):
    """Use case for archiving tasks.

    Supports two archiving modes:
    - Orphan mode (default): Archives task and sets children's parent_id to None
    - Cascade mode: Recursively archives task and all its descendants

    Returns the number of tasks archived.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: ArchiveTaskInput) -> int:
        """Execute task archiving.

        Args:
            input_dto: Task archiving input data

        Returns:
            Number of tasks archived

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        self._get_task_or_raise(self.repository, input_dto.task_id)

        if input_dto.cascade:
            return self._archive_cascade(input_dto.task_id)
        else:
            return self._archive_orphan(input_dto.task_id)

    def _archive_cascade(self, task_id: int) -> int:
        """Recursively archive task and all its children.

        Args:
            task_id: ID of the task to archive

        Returns:
            Number of tasks archived
        """
        archived_count = 0

        # Recursively archive all children first
        children = self.repository.get_children(task_id)
        for child in children:
            assert child.id is not None  # Children from repository always have IDs
            archived_count += self._archive_cascade(child.id)

        # Archive the task itself
        task = self.repository.get_by_id(task_id)
        if task is None:
            return archived_count  # Task was deleted, skip
        task.status = TaskStatus.ARCHIVED
        self.repository.save(task)
        archived_count += 1

        return archived_count

    def _archive_orphan(self, task_id: int) -> int:
        """Archive task and orphan its children.

        Args:
            task_id: ID of the task to archive

        Returns:
            Number of tasks archived (always 1)
        """
        # Orphan children (set their parent_id to None)
        children = self.repository.get_children(task_id)
        for child in children:
            child.parent_id = None
            self.repository.save(child)

        # Archive the task itself
        task = self.repository.get_by_id(task_id)
        if task is None:
            return 0  # Task was deleted, skip
        task.status = TaskStatus.ARCHIVED
        self.repository.save(task)

        return 1
