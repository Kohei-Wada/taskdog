"""Output DTO for status change operations."""

from dataclasses import dataclass

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus


@dataclass(frozen=True)
class StatusChangeOutput:
    """Output DTO that wraps TaskOperationOutput with the previous status.

    Used by StatusChangeUseCase to return both the updated task and
    the status before the change, eliminating the need for callers
    to hardcode or guess the old status.

    Attributes:
        task: The updated task operation output
        old_status: The task's status before the change
    """

    task: TaskOperationOutput
    old_status: TaskStatus
