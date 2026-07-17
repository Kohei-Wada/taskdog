"""Task DTOs for data transfer between layers.

This module contains DTOs that represent task data without exposing
the Task entity directly to the presentation layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from taskdog_core.domain.entities.task import TaskStatus

if TYPE_CHECKING:
    from taskdog_core.domain.entities.task import Task


class TaskSummaryDto(BaseModel):
    """Minimal task information for lists and references.

    Used when only basic task identification is needed.
    Includes optional duration fields for statistics display.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    estimated_duration: float | None = None
    actual_duration_hours: float | None = None

    @classmethod
    def from_entity(cls, task: Task) -> TaskSummaryDto:
        """Convert Task entity to TaskSummaryDto.

        Args:
            task: Task entity to convert

        Returns:
            TaskSummaryDto with id, name, and duration fields

        Raises:
            ValueError: If task.id is None
        """
        if task.id is None:
            raise ValueError("Task must have an ID")
        return cls(
            id=task.id,
            name=task.name,
            estimated_duration=task.estimated_duration,
            actual_duration_hours=task.actual_duration_hours,
        )


class TaskRowDto(BaseModel):
    """Task data for table row display.

    Contains all fields needed for table visualization.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    priority: int | None
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
    daily_allocations: dict[date, float] = Field(default_factory=dict)
    is_archived: bool
    is_finished: bool
    created_at: datetime
    updated_at: datetime
    has_notes: bool = False

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
            daily_allocations=task.daily_allocations,
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
        return self.model_dump(mode="json")


class TaskDetailDto(BaseModel):
    """Complete task information for detail views.

    Contains all task data needed for display and editing,
    without exposing the Task entity.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    priority: int | None
    status: TaskStatus
    planned_start: datetime | None
    planned_end: datetime | None
    deadline: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    actual_duration: float | None = None
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
            actual_duration=task.actual_duration,
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
