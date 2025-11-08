"""Output DTO for get_task_by_id query.

This DTO wraps task detail data for single task retrieval queries.
"""

from dataclasses import dataclass

from taskdog_core.application.dto.task_dto import TaskDetailDto


@dataclass
class GetTaskByIdOutput:
    """Output DTO for single task retrieval by ID.

    Used by QueryController.get_task_by_id() and consumed by TUI commands.

    Attributes:
        task: Task detail DTO (None if task not found)
    """

    task: TaskDetailDto | None
