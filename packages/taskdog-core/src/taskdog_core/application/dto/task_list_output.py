"""Output DTO for task list queries.

This DTO provides a presentation-agnostic representation of task list query results,
containing the filtered tasks along with metadata for pagination and statistics.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from taskdog_core.application.dto.task_dto import TaskRowDto

if TYPE_CHECKING:
    from taskdog_core.application.dto.gantt_output import GanttOutput


@dataclass
class TaskListOutput:
    """Output DTO for task list queries.

    Contains filtered and sorted tasks along with count metadata.
    Used by table, today, week commands and future API endpoints.

    Attributes:
        tasks: Filtered and sorted list of task DTOs
        total_count: Total number of tasks in repository (before filtering)
        filtered_count: Number of tasks after filtering
        gantt_data: Optional Gantt chart data (when requested via include_gantt)
    """

    tasks: list[TaskRowDto]
    total_count: int
    filtered_count: int
    gantt_data: "GanttOutput | None" = None
