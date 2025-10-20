"""Helper functions for managing task dependencies in TUI."""

from application.dto.manage_dependencies_request import (
    AddDependencyRequest,
    RemoveDependencyRequest,
)
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from domain.exceptions.task_exceptions import TaskValidationError
from infrastructure.persistence.task_repository import TaskRepository


def add_dependencies(
    task_id: int, dependency_ids: list[int], repository: TaskRepository
) -> list[tuple[int, str]]:
    """Add multiple dependencies to a task.

    Args:
        task_id: ID of the task to add dependencies to
        dependency_ids: List of dependency task IDs to add
        repository: Task repository for data access

    Returns:
        List of (dependency_id, error_message) tuples for failed additions.
        Empty list if all succeeded.
    """
    if not dependency_ids:
        return []

    use_case = AddDependencyUseCase(repository)
    failed_dependencies = []

    for dep_id in dependency_ids:
        try:
            dependency_input = AddDependencyRequest(task_id=task_id, depends_on_id=dep_id)
            use_case.execute(dependency_input)
        except TaskValidationError as e:
            failed_dependencies.append((dep_id, str(e)))

    return failed_dependencies


def sync_dependencies(
    task_id: int,
    old_dependency_ids: set[int],
    new_dependency_ids: set[int],
    repository: TaskRepository,
) -> list[str]:
    """Synchronize task dependencies by adding/removing as needed.

    Args:
        task_id: ID of the task to sync dependencies for
        old_dependency_ids: Set of current dependency IDs
        new_dependency_ids: Set of desired dependency IDs
        repository: Task repository for data access

    Returns:
        List of error messages for failed operations.
        Empty list if all operations succeeded.
    """
    # Calculate differences
    deps_to_remove = old_dependency_ids - new_dependency_ids
    deps_to_add = new_dependency_ids - old_dependency_ids

    failed_operations = []

    # Remove dependencies
    if deps_to_remove:
        remove_use_case = RemoveDependencyUseCase(repository)
        for dep_id in deps_to_remove:
            try:
                remove_input = RemoveDependencyRequest(task_id=task_id, depends_on_id=dep_id)
                remove_use_case.execute(remove_input)
            except TaskValidationError as e:
                failed_operations.append(f"Remove {dep_id}: {e}")

    # Add dependencies
    if deps_to_add:
        add_use_case = AddDependencyUseCase(repository)
        for dep_id in deps_to_add:
            try:
                add_input = AddDependencyRequest(task_id=task_id, depends_on_id=dep_id)
                add_use_case.execute(add_input)
            except TaskValidationError as e:
                failed_operations.append(f"Add {dep_id}: {e}")

    return failed_operations
