"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.services.hierarchy_operation_service import HierarchyOperationService
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
        self.hierarchy_service = HierarchyOperationService()

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

        # Define the archive operation
        def archive_operation(task_id: int) -> None:
            task = self.repository.get_by_id(task_id)
            if task is not None:  # Skip if task was deleted
                task.status = TaskStatus.ARCHIVED
                self.repository.save(task)

        # Execute using hierarchy service
        if input_dto.cascade:
            return self.hierarchy_service.execute_cascade(
                input_dto.task_id, self.repository, archive_operation
            )
        else:
            return self.hierarchy_service.execute_orphan(
                input_dto.task_id, self.repository, archive_operation
            )
