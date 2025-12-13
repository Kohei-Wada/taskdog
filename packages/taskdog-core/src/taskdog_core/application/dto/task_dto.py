"""Task DTOs for data transfer between layers.

This module contains DTOs that represent task data without exposing
the Task entity directly to the presentation layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from taskdog_core.domain.entities.task import TaskStatus

if TYPE_CHECKING:
    from taskdog_core.domain.entities.task import Task


@dataclass(frozen=True)
class TaskSummaryDto:
    """Minimal task information for lists and references.

    Used when only basic task identification is needed.
    """

    id: int
    name: str

    @classmethod
    def from_entity(cls, task: Task) -> TaskSummaryDto:
        """Convert Task entity to TaskSummaryDto.

        Args:
            task: Task entity to convert

        Returns:
            TaskSummaryDto with id and name

        Raises:
            ValueError: If task.id is None
        """
        if task.id is None:
            raise ValueError("Task must have an ID")
        return cls(id=task.id, name=task.name)


@dataclass(frozen=True)
class GanttTaskDto:
    """Task data for Gantt chart display.

    Contains only the fields needed for Gantt visualization.
    """

    id: int
    name: str
    status: TaskStatus
    estimated_duration: float | None
    planned_start: datetime | None
    planned_end: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    deadline: datetime | None
    is_finished: bool

    @classmethod
    def from_entity(cls, task: Task) -> GanttTaskDto:
        """Convert Task entity to GanttTaskDto.

        Args:
            task: Task entity to convert

        Returns:
            GanttTaskDto with fields needed for Gantt visualization

        Raises:
            ValueError: If task.id is None
        """
        if task.id is None:
            raise ValueError("Task must have an ID")

        return cls(
            id=task.id,
            name=task.name,
            status=task.status,
            estimated_duration=task.estimated_duration,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            deadline=task.deadline,
            is_finished=task.is_finished,
        )


@dataclass(frozen=True)
class TaskRowDto:
    """Task data for table row display.

    Contains all fields needed for table visualization.
    """

    id: int
    name: str
    priority: int
    status: TaskStatus
    planned_start: datetime | None
    planned_end: datetime | None
    deadline: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    estimated_duration: float | None
    actual_duration_hours: float | None
    is_fixed: bool
    depends_on: list[int]
    tags: list[str]
    is_archived: bool
    is_finished: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, task: Task) -> TaskRowDto:
        """Convert Task entity to TaskRowDto.

        Args:
            task: Task entity to convert

        Returns:
            TaskRowDto with fields needed for table display

        Raises:
            ValueError: If task.id is None
        """
        if task.id is None:
            raise ValueError("Task must have an ID")

        return cls(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            actual_duration_hours=task.actual_duration_hours,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            tags=task.tags,
            is_archived=task.is_archived,
            is_finished=task.is_finished,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def to_dict(self) -> dict[str, object]:
        """Convert DTO to dictionary for export purposes.

        Returns:
            Dictionary with all task fields, using string values for enums and ISO format for datetimes.
        """
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "status": self.status.value,
            "planned_start": self.planned_start.isoformat()
            if self.planned_start
            else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "actual_start": self.actual_start.isoformat()
            if self.actual_start
            else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "estimated_duration": self.estimated_duration,
            "actual_duration_hours": self.actual_duration_hours,
            "is_fixed": self.is_fixed,
            "depends_on": self.depends_on,
            "tags": self.tags,
            "is_archived": self.is_archived,
            "is_finished": self.is_finished,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class TaskDetailDto:
    """Complete task information for detail views.

    Contains all task data needed for display and editing,
    without exposing the Task entity.
    """

    id: int
    name: str
    priority: int
    status: TaskStatus
    planned_start: datetime | None
    planned_end: datetime | None
    deadline: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    estimated_duration: float | None
    daily_allocations: dict[date, float]
    is_fixed: bool
    depends_on: list[int]
    tags: list[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    # Computed properties from Task entity
    actual_duration_hours: float | None
    is_active: bool
    is_finished: bool
    can_be_modified: bool
    is_schedulable: bool

    @classmethod
    def from_entity(cls, task: Task, force_override: bool = False) -> TaskDetailDto:
        """Convert Task entity to TaskDetailDto.

        Args:
            task: Task entity to convert
            force_override: Whether to allow rescheduling for is_schedulable check

        Returns:
            TaskDetailDto with all task data and computed properties

        Raises:
            ValueError: If task.id is None
        """
        if task.id is None:
            raise ValueError("Task must have an ID")

        return cls(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            daily_allocations=task.daily_allocations,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            tags=task.tags,
            is_archived=task.is_archived,
            created_at=task.created_at,
            updated_at=task.updated_at,
            actual_duration_hours=task.actual_duration_hours,
            is_active=task.is_active,
            is_finished=task.is_finished,
            can_be_modified=task.can_be_modified,
            is_schedulable=task.is_schedulable(force_override=force_override),
        )
