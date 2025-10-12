"""Base class for use cases."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from domain.entities.task import Task
    from infrastructure.persistence.task_repository import TaskRepository

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class UseCase(ABC, Generic[TInput, TOutput]):
    """Abstract base class for use cases.

    Use cases encapsulate business logic and orchestrate operations
    between domain entities and infrastructure services.

    Type Parameters:
        TInput: The input DTO type for the use case
        TOutput: The output type (usually a domain entity or DTO)

    Example:
        class CreateTaskUseCase(UseCase[CreateTaskInput, Task]):
            def execute(self, input_dto: CreateTaskInput) -> Task:
                # Validation
                # Business logic
                # Persistence
                return task
    """

    @abstractmethod
    def execute(self, input_dto: TInput) -> TOutput:
        """Execute the use case with the given input.

        Args:
            input_dto: Input data for the use case

        Returns:
            Result of the use case execution

        Raises:
            Domain-specific exceptions as needed
        """
        pass

    def _get_task_or_raise(self, repository: "TaskRepository", task_id: int) -> "Task":
        """Get task by ID or raise TaskNotFoundException.

        Args:
            repository: Task repository
            task_id: Task ID to retrieve

        Returns:
            Task instance

        Raises:
            TaskNotFoundException: If task not found
        """
        from domain.exceptions.task_exceptions import TaskNotFoundException

        task = repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException(task_id)
        return task
