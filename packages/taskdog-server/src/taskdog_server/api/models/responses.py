"""Pydantic response models for FastAPI endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from taskdog_core.domain.entities.task import TaskStatus

if TYPE_CHECKING:
    from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
    from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
    from taskdog_core.application.dto.update_task_output import TaskUpdateOutput


class TaskFieldsBase(BaseModel):
    """Common fields shared by all task Response models."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: TaskStatus
    priority: int | None = None
    deadline: datetime | None = None
    estimated_duration: float | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    actual_duration_hours: float | None = None
    depends_on: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_fixed: bool = False
    is_archived: bool = False


class TaskOperationResponse(TaskFieldsBase):
    """Response model for task write operations (create, update, status changes)."""

    actual_duration: float | None = None

    @classmethod
    def from_dto(cls, dto: TaskOperationOutput) -> TaskOperationResponse:
        """Convert TaskOperationOutput DTO to response model.

        Args:
            dto: TaskOperationOutput from use case

        Returns:
            TaskOperationResponse for API response
        """
        return cls.model_validate(dto)


class UpdateTaskResponse(TaskOperationResponse):
    """Response model for task update operations (PATCH). Includes updated_fields."""

    updated_fields: list[str] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: TaskUpdateOutput) -> UpdateTaskResponse:  # type: ignore[override]
        """Convert TaskUpdateOutput DTO to response model.

        Args:
            dto: TaskUpdateOutput from use case

        Returns:
            UpdateTaskResponse for API response
        """
        return cls.model_validate(dto.task).model_copy(
            update={"updated_fields": dto.updated_fields}
        )


class TaskReadResponseBase(TaskFieldsBase):
    """Common fields for read-oriented Response models."""

    model_config = ConfigDict(frozen=True)

    is_finished: bool = False
    has_notes: bool = False
    created_at: datetime
    updated_at: datetime


class TaskResponse(TaskReadResponseBase):
    """Response model for task row data (list views)."""


class TaskDetailResponse(TaskReadResponseBase):
    """Response model for detailed task view."""

    daily_allocations: dict[str, float] = Field(default_factory=dict)
    is_active: bool = False
    can_be_modified: bool = False
    is_schedulable: bool = False
    notes: str | None = None

    @field_validator("daily_allocations", mode="before")
    @classmethod
    def _isoformat_allocation_keys(cls, value: Any) -> Any:
        """Convert date keys (from the DTO) to ISO format strings."""
        if isinstance(value, dict):
            return {
                key.isoformat() if isinstance(key, date) else key: hours
                for key, hours in value.items()
            }
        return value

    @classmethod
    def from_dto(cls, dto: TaskDetailOutput) -> TaskDetailResponse:
        """Convert TaskDetailOutput DTO to response model.

        Args:
            dto: TaskDetailOutput from use case

        Returns:
            TaskDetailResponse for API response
        """
        return cls.model_validate(dto.task).model_copy(
            update={"has_notes": dto.has_notes, "notes": dto.notes_content}
        )


class BulkTaskResult(BaseModel):
    """Result for a single task in a bulk operation."""

    task_id: int
    success: bool
    task: TaskOperationResponse | None = None
    error: str | None = None


class BulkOperationResponse(BaseModel):
    """Response model for bulk task operations."""

    results: list[BulkTaskResult]


class TaskListResponse(BaseModel):
    """Response model for task list queries."""

    tasks: list[TaskResponse]
    total_count: int
    filtered_count: int
    gantt: GanttResponse | None = None


class GanttDateRange(BaseModel):
    """Date range for Gantt chart."""

    start_date: date
    end_date: date


class GanttResponse(BaseModel):
    """Gantt overlay data, joined to the shared task list by id.

    Task fields are not duplicated here; clients join this overlay with the
    ``tasks`` list from the same response using ``task.id``.
    """

    date_range: GanttDateRange
    task_daily_hours: dict[int, dict[str, float]]
    daily_workload: dict[str, float]
    holidays: list[str] = Field(default_factory=list)
    total_estimated_duration: float = 0.0


class CompletionStatistics(BaseModel):
    """Completion rate statistics."""

    total: int
    completed: int
    in_progress: int
    pending: int
    canceled: int
    completion_rate: float


class TaskSummaryResponse(BaseModel):
    """Minimal task information for references.

    Includes optional duration fields for statistics display.
    """

    id: int
    name: str
    estimated_duration: float | None = None
    actual_duration_hours: float | None = None


class TimeStatistics(BaseModel):
    """Time tracking statistics."""

    total_work_hours: float
    average_work_hours: float | None = None
    median_work_hours: float = 0.0
    longest_task: TaskSummaryResponse | None = None
    shortest_task: TaskSummaryResponse | None = None
    tasks_with_time_tracking: int = 0


class EstimationStatistics(BaseModel):
    """Estimation accuracy statistics."""

    total_tasks_with_estimation: int
    accuracy_rate: float = 0.0
    over_estimated_count: int = 0
    under_estimated_count: int = 0
    exact_count: int = 0
    best_estimated_tasks: list[TaskSummaryResponse] = Field(default_factory=list)
    worst_estimated_tasks: list[TaskSummaryResponse] = Field(default_factory=list)


class DeadlineStatistics(BaseModel):
    """Deadline compliance statistics."""

    total_tasks_with_deadline: int
    met_deadline_count: int
    missed_deadline_count: int
    compliance_rate: float
    average_delay_days: float = 0.0


class PriorityDistribution(BaseModel):
    """Task distribution by priority."""

    distribution: dict[int, int]
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    high_priority_completion_rate: float = 0.0


class TrendData(BaseModel):
    """Trend data over time."""

    last_7_days_completed: int = 0
    last_30_days_completed: int = 0
    weekly_completion_trend: dict[str, int] = Field(default_factory=dict)
    monthly_completion_trend: dict[str, int] = Field(default_factory=dict)


class StatisticsResponse(BaseModel):
    """Response model for task statistics."""

    completion: CompletionStatistics
    time: TimeStatistics | None = None
    estimation: EstimationStatistics | None = None
    deadline: DeadlineStatistics | None = None
    priority: PriorityDistribution
    trends: TrendData | None = None


class TagStatisticsItem(BaseModel):
    """Statistics for a single tag."""

    tag: str
    count: int
    completion_rate: float


class TagStatisticsResponse(BaseModel):
    """Response model for tag statistics."""

    tags: list[TagStatisticsItem]
    total_tags: int


class SchedulingFailure(BaseModel):
    """Information about a task that failed to be scheduled."""

    task_id: int
    task_name: str
    reason: str


class OptimizationSummary(BaseModel):
    """Summary of optimization results."""

    total_tasks: int
    scheduled_tasks: int
    failed_tasks: int
    total_hours: float
    start_date: date
    end_date: date
    algorithm: str


class OptimizationResponse(BaseModel):
    """Response model for schedule optimization."""

    summary: OptimizationSummary
    failures: list[SchedulingFailure] = Field(default_factory=list)
    message: str


class NotesResponse(BaseModel):
    """Response model for task notes."""

    task_id: int
    content: str
    has_notes: bool


class DeleteTagResponse(BaseModel):
    """Response model for tag deletion."""

    tag_name: str
    affected_task_count: int


class AuditLogResponse(BaseModel):
    """Response model for a single audit log entry."""

    id: int
    timestamp: datetime
    client_name: str | None = None
    operation: str
    resource_type: str
    resource_id: int | None = None
    resource_name: str | None = None
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    success: bool
    error_message: str | None = None


class AuditLogListResponse(BaseModel):
    """Response model for audit log list queries."""

    logs: list[AuditLogResponse]
    total_count: int
    limit: int
    offset: int
