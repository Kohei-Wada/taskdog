"""Output DTOs for bulk task operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@dataclass(frozen=True)
class BulkTaskResultOutput:
    """Result for a single task within a bulk operation.

    Attributes:
        task_id: ID of the task that was operated on
        success: Whether the operation succeeded
        task: Task operation output if successful
        error: Error message if failed
    """

    task_id: int
    success: bool
    task: TaskOperationOutput | None = None
    error: str | None = None


@dataclass(frozen=True)
class BulkOperationOutput:
    """Output for a bulk task operation.

    Attributes:
        operation: Name of the operation performed
        total: Total number of tasks requested
        succeeded: Number of successful operations
        failed: Number of failed operations
        results: Per-task results
    """

    operation: str
    total: int
    succeeded: int
    failed: int
    results: tuple[BulkTaskResultOutput, ...]
