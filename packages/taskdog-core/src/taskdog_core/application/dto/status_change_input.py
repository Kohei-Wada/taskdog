"""Protocol for status change input DTOs."""

from typing import Protocol


class StatusChangeInput(Protocol):
    """Protocol for status change input DTOs.

    All status change input DTOs (StartTaskInput, CompleteTaskInput, etc.)
    must have a task_id field to identify which task to update.

    This protocol is used as a type constraint in StatusChangeUseCase
    to ensure type safety across all status change operations.
    """

    task_id: int
