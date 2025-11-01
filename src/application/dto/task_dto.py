"""Task DTOs for data transfer between layers.

This module contains DTOs that represent task data without exposing
the Task entity directly to the presentation layer.
"""

from dataclasses import dataclass
from datetime import date, datetime

from domain.entities.task import TaskStatus


@dataclass(frozen=True)
class TaskSummaryDto:
    """Minimal task information for lists and references.

    Used when only basic task identification is needed.
    """

    id: int
    name: str


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
    actual_daily_hours: dict[date, float]
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
