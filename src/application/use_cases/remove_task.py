"""Use case for removing a task."""

from application.dto.remove_task_input import RemoveTaskInput
from application.services.estimated_duration_propagator import EstimatedDurationPropagator
from application.services.hierarchy_operation_service import HierarchyOperationService
from application.use_cases.base import UseCase
from infrastructure.persistence.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[RemoveTaskInput, int]):
    """Use case for removing tasks.

    Supports two removal modes:
    - Orphan mode (default): Removes task and sets children's parent_id to None
    - Cascade mode: Recursively removes task and all its descendants

    After removal, automatically updates parent's estimated_duration.
    Returns the number of tasks removed.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
        self.hierarchy_service = HierarchyOperationService()
        self.duration_propagator = EstimatedDurationPropagator(repository)

    def execute(self, input_dto: RemoveTaskInput) -> int:
        """Execute task removal.

        Args:
            input_dto: Task removal input data

        Returns:
            Number of tasks removed

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Remember parent_id before deletion to update parent's estimated_duration
        parent_id_to_update = task.parent_id

        # Define the delete operation
        def delete_operation(task_id: int) -> None:
            self.repository.delete(task_id)

        # Execute using hierarchy service
        if input_dto.cascade:
            removed_count = self.hierarchy_service.execute_cascade(
                input_dto.task_id, self.repository, delete_operation
            )
        else:
            removed_count = self.hierarchy_service.execute_orphan(
                input_dto.task_id, self.repository, delete_operation
            )

        # Update parent's estimated_duration after removal
        if parent_id_to_update is not None:
            self.duration_propagator.propagate(parent_id_to_update)

        return removed_count
