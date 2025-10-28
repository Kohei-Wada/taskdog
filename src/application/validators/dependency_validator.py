"""Validator for task dependencies."""

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import DependencyNotMetError
from infrastructure.persistence.task_repository import TaskRepository


class DependencyValidator:
    """Validator for task dependency constraints.

    Business Rules:
    - All dependencies must exist in the repository
    - All dependencies must have COMPLETED status
    - Tasks without dependencies always pass validation
    """

    @staticmethod
    def validate_dependencies_met(task: Task, repository: TaskRepository) -> None:
        """Validate that all task dependencies are met.

        Args:
            task: Task to validate dependencies for
            repository: Repository to look up dependency tasks

        Raises:
            DependencyNotMetError: If any dependency is not met
        """
        # task.id should always be set when this validator is called
        assert task.id is not None

        # No dependencies to check
        if not task.depends_on:
            return

        # Batch fetch all dependencies at once (prevents N+1 query problem)
        dep_tasks = repository.get_by_ids(task.depends_on)

        # Collect unmet dependencies
        unmet_dependency_ids = []
        for dep_id in task.depends_on:
            dep_task = dep_tasks.get(dep_id)
            if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
                # Dependency doesn't exist or is not completed
                unmet_dependency_ids.append(dep_id)

        # Raise error if any dependencies are unmet
        if unmet_dependency_ids:
            raise DependencyNotMetError(
                task_id=task.id,
                unmet_dependencies=unmet_dependency_ids,
            )
