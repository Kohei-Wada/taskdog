"""Pydantic request models for FastAPI endpoints."""

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from domain.entities.task import TaskStatus


class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""

    name: str = Field(..., min_length=1, description="Task name")
    priority: int | None = Field(None, gt=0, description="Task priority (higher = more important)")
    planned_start: datetime | None = Field(None, description="Planned start datetime")
    planned_end: datetime | None = Field(None, description="Planned end datetime")
    deadline: datetime | None = Field(None, description="Task deadline")
    estimated_duration: float | None = Field(None, gt=0, description="Estimated duration in hours")
    is_fixed: bool = Field(False, description="Whether schedule is fixed")
    tags: list[str] | None = Field(None, description="List of tags")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate tags are non-empty and unique."""
        if v is not None:
            if any(not tag.strip() for tag in v):
                raise ValueError("Tags must be non-empty")
            if len(v) != len(set(v)):
                raise ValueError("Tags must be unique")
        return v


class UpdateTaskRequest(BaseModel):
    """Request model for updating a task.

    All fields are optional. Only provided fields will be updated.
    """

    name: str | None = Field(None, min_length=1, description="New task name")
    priority: int | None = Field(None, gt=0, description="New priority")
    status: TaskStatus | None = Field(None, description="New status")
    planned_start: datetime | None = Field(None, description="New planned start")
    planned_end: datetime | None = Field(None, description="New planned end")
    deadline: datetime | None = Field(None, description="New deadline")
    estimated_duration: float | None = Field(None, gt=0, description="New estimated duration")
    is_fixed: bool | None = Field(None, description="New fixed status")
    tags: list[str] | None = Field(None, description="New tags list")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate tags are non-empty and unique."""
        if v is not None:
            if any(not tag.strip() for tag in v):
                raise ValueError("Tags must be non-empty")
            if len(v) != len(set(v)):
                raise ValueError("Tags must be unique")
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
        if any(not tag.strip() for tag in v):
            raise ValueError("Tags must be non-empty")
        if len(v) != len(set(v)):
            raise ValueError("Tags must be unique")
        return v


class LogHoursRequest(BaseModel):
    """Request model for logging actual hours worked."""

    hours: float = Field(..., gt=0, description="Hours worked")
    date: date_type | None = Field(None, description="Date of work (defaults to today)")


class OptimizeScheduleRequest(BaseModel):
    """Request model for schedule optimization."""

    algorithm: str = Field(..., description="Algorithm name (e.g., 'greedy', 'balanced')")
    start_date: datetime | None = Field(None, description="Optimization start date")
    max_hours_per_day: float | None = Field(None, gt=0, le=24, description="Maximum hours per day")
    force_override: bool = Field(
        True, description="Whether to override existing schedules for non-fixed tasks"
    )


class TaskFilterParams(BaseModel):
    """Query parameters for filtering tasks."""

    all: bool = Field(False, description="Include archived tasks")
    status: TaskStatus | None = Field(None, description="Filter by status")
    tags: list[str] | None = Field(None, description="Filter by tags (OR logic)")
    start_date: date_type | None = Field(
        None, description="Filter by start date (tasks on or after)"
    )
    end_date: date_type | None = Field(None, description="Filter by end date (tasks on or before)")


class TaskSortParams(BaseModel):
    """Query parameters for sorting tasks."""

    sort: str = Field("id", description="Sort field (id, name, priority, deadline, etc.)")
    reverse: bool = Field(False, description="Reverse sort order")
