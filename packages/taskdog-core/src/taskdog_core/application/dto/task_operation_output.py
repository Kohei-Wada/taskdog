"""Output DTO for task write operations."""

from dataclasses import dataclass
from datetime import datetime

from taskdog_core.domain.entities.task import Task, TaskStatus


@dataclass
class TaskOperationOutput:
    """Generic output DTO for task write operations.

    This DTO is used by TaskController to return task operation results
    without exposing domain entities to the presentation layer. It contains
    all commonly accessed task fields needed for CLI/TUI display.

    Attributes:
        id: Task ID
        name: Task name
        status: Task status
        priority: Task priority
        deadline: Task deadline
        estimated_duration: Estimated duration in hours
        planned_start: Planned start datetime
        planned_end: Planned end datetime
        actual_start: Actual start datetime (for started tasks)
        actual_end: Actual end datetime (for completed/canceled tasks)
        depends_on: List of dependency task IDs
        tags: List of tags
        is_fixed: Whether task schedule is fixed
        is_archived: Whether task is archived (soft deleted)
        actual_duration_hours: Computed actual duration (for completed tasks)
        daily_allocations: Dictionary mapping dates to allocated hours (from optimization)
    """

    id: int
    name: str
    status: TaskStatus
    priority: int
    deadline: datetime | None
    estimated_duration: float | None
    planned_start: datetime | None
    planned_end: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    depends_on: list[int]
    tags: list[str]
    is_fixed: bool
    is_archived: bool
    actual_duration_hours: float | None
    daily_allocations: dict[str, float]

    @classmethod
    def from_task(cls, task: Task) -> "TaskOperationOutput":
        """Convert Task entity to DTO.

        Args:
            task: Task entity from domain layer

        Returns:
            TaskOperationOutput DTO for presentation layer

        Raises:
            ValueError: If task.id is None
        """
        # Type narrowing
        if task.id is None:
            raise ValueError("Cannot convert task without ID to DTO")

        return cls(
            id=task.id,
            name=task.name,
            status=task.status,
            priority=task.priority,
            deadline=task.deadline,
            estimated_duration=task.estimated_duration,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            depends_on=task.depends_on,
            tags=task.tags,
            is_fixed=task.is_fixed,
            is_archived=task.is_archived,
            actual_duration_hours=task.actual_duration_hours,
            daily_allocations={
                date.isoformat(): hours
                for date, hours in task.daily_allocations.items()
            },
        )
