"""Base class for use cases."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

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
