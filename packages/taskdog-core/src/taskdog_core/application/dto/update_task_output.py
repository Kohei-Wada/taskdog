"""Output DTO for update_task operation."""

from dataclasses import dataclass

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import Task


@dataclass
class TaskUpdateOutput:
    """Output DTO for update_task operation.

    This DTO wraps TaskOperationOutput and adds metadata about which
    fields were updated during the operation.

    Attributes:
        task: The updated task information
        updated_fields: List of field names that were updated
    """

    task: TaskOperationOutput
    updated_fields: list[str]

    @classmethod
    def from_task_and_fields(
        cls, task: Task, updated_fields: list[str]
    ) -> "TaskUpdateOutput":
        """Convert Task entity and field list to DTO.

        Args:
            task: Updated task entity from domain layer
            updated_fields: List of field names that were updated

        Returns:
            TaskUpdateOutput DTO for presentation layer
        """
        return cls(
            task=TaskOperationOutput.from_task(task),
            updated_fields=updated_fields,
        )
