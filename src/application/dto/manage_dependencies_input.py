"""DTO for managing task dependencies."""

from dataclasses import dataclass


@dataclass
class AddDependencyInput:
    """Input data for adding a task dependency.

    Attributes:
        task_id: ID of the task that depends on another
        depends_on_id: ID of the task that must be completed first
    """

    task_id: int
    depends_on_id: int


@dataclass
class RemoveDependencyInput:
    """Input data for removing a task dependency.

    Attributes:
        task_id: ID of the task
        depends_on_id: ID of the dependency to remove
    """

    task_id: int
    depends_on_id: int
