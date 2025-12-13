"""Pydantic request models for FastAPI endpoints."""

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.shared.constants import MAX_TASK_NAME_LENGTH
from taskdog_server.api.validators import validate_tags as _validate_tags


class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""

    name: str = Field(
        ..., min_length=1, max_length=MAX_TASK_NAME_LENGTH, description="Task name"
    )
    priority: int | None = Field(
        None, gt=0, description="Task priority (higher = more important)"
    )
    planned_start: datetime | None = Field(None, description="Planned start datetime")
    planned_end: datetime | None = Field(None, description="Planned end datetime")
    deadline: datetime | None = Field(None, description="Task deadline")
    estimated_duration: float | None = Field(
        None, gt=0, description="Estimated duration in hours"
    )
    is_fixed: bool = Field(False, description="Whether schedule is fixed")
    tags: list[str] | None = Field(None, description="List of tags")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate tags are non-empty and unique."""
        if v is not None:
            return _validate_tags(v)
        return v


class UpdateTaskRequest(BaseModel):
    """Request model for updating a task.

    All fields are optional. Only provided fields will be updated.
    """

    name: str | None = Field(
        None, min_length=1, max_length=MAX_TASK_NAME_LENGTH, description="New task name"
    )
    priority: int | None = Field(None, gt=0, description="New priority")
    status: TaskStatus | None = Field(None, description="New status")
    planned_start: datetime | None = Field(None, description="New planned start")
    planned_end: datetime | None = Field(None, description="New planned end")
    deadline: datetime | None = Field(None, description="New deadline")
    estimated_duration: float | None = Field(
        None, gt=0, description="New estimated duration"
    )
    is_fixed: bool | None = Field(None, description="New fixed status")
    tags: list[str] | None = Field(None, description="New tags list")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate tags are non-empty and unique."""
        if v is not None:
            return _validate_tags(v)
        return v


class AddDependencyRequest(BaseModel):
    """Request model for adding a task dependency."""

    depends_on_id: int = Field(..., description="ID of the task this task depends on")


class SetTaskTagsRequest(BaseModel):
    """Request model for setting task tags."""

    tags: list[str] = Field(..., description="List of tags to set")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty and unique."""
        return _validate_tags(v)


class FixActualTimesRequest(BaseModel):
    """Request model for fixing actual timestamps and duration.

    Used to correct actual_start, actual_end, and actual_duration
    after the fact, for historical accuracy. Past dates are allowed.
    """

    actual_start: datetime | None = Field(
        None, description="New actual start datetime (null to clear)"
    )
    actual_end: datetime | None = Field(
        None, description="New actual end datetime (null to clear)"
    )
    actual_duration: float | None = Field(
        None, description="Explicit duration in hours (overrides calculated value)"
    )
    clear_start: bool = Field(
        False, description="Clear actual_start (mutually exclusive with actual_start)"
    )
    clear_end: bool = Field(
        False, description="Clear actual_end (mutually exclusive with actual_end)"
    )
    clear_duration: bool = Field(
        False,
        description="Clear actual_duration (mutually exclusive with actual_duration)",
    )

    @model_validator(mode="after")
    def validate_exclusive_options(self) -> "FixActualTimesRequest":
        """Validate mutually exclusive options and ensure at least one operation."""
        if self.actual_start is not None and self.clear_start:
            raise ValueError("Cannot set actual_start and clear_start simultaneously")
        if self.actual_end is not None and self.clear_end:
            raise ValueError("Cannot set actual_end and clear_end simultaneously")
        if self.actual_duration is not None and self.clear_duration:
            raise ValueError(
                "Cannot set actual_duration and clear_duration simultaneously"
            )

        # Validate duration is positive
        if self.actual_duration is not None and self.actual_duration <= 0:
            raise ValueError("actual_duration must be greater than 0")

        # Ensure at least one operation is specified
        if (
            self.actual_start is None
            and self.actual_end is None
            and self.actual_duration is None
            and not self.clear_start
            and not self.clear_end
            and not self.clear_duration
        ):
            raise ValueError(
                "At least one of actual_start, actual_end, actual_duration, "
                "clear_start, clear_end, or clear_duration must be specified"
            )

        return self


class OptimizeScheduleRequest(BaseModel):
    """Request model for schedule optimization."""

    algorithm: str = Field(
        ..., description="Algorithm name (e.g., 'greedy', 'balanced')"
    )
    start_date: datetime | None = Field(None, description="Optimization start date")
    max_hours_per_day: float | None = Field(
        None, gt=0, le=24, description="Maximum hours per day"
    )
    force_override: bool = Field(
        True, description="Whether to override existing schedules for non-fixed tasks"
    )
    task_ids: list[int] | None = Field(
        None,
        description="Specific task IDs to optimize (None means all schedulable tasks)",
    )


class TaskFilterParams(BaseModel):
    """Query parameters for filtering tasks."""

    all: bool = Field(False, description="Include archived tasks")
    status: TaskStatus | None = Field(None, description="Filter by status")
    tags: list[str] | None = Field(None, description="Filter by tags (OR logic)")
    start_date: date_type | None = Field(
        None, description="Filter by start date (tasks on or after)"
    )
    end_date: date_type | None = Field(
        None, description="Filter by end date (tasks on or before)"
    )


class TaskSortParams(BaseModel):
    """Query parameters for sorting tasks."""

    sort: str = Field(
        "id", description="Sort field (id, name, priority, deadline, etc.)"
    )
    reverse: bool = Field(False, description="Reverse sort order")


class UpdateNotesRequest(BaseModel):
    """Request model for updating task notes."""

    content: str = Field(..., description="Notes content (markdown)")
