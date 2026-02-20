"""Pydantic response models for FastAPI endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from taskdog_core.domain.entities.task import TaskStatus

if TYPE_CHECKING:
    from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
    from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
    from taskdog_core.application.dto.update_task_output import TaskUpdateOutput


class TaskOperationResponse(BaseModel):
    """Response model for task write operations (create, update, status changes)."""

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
    actual_duration: float | None = None
    depends_on: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_fixed: bool = False
    is_archived: bool = False
    actual_duration_hours: float | None = None

    @classmethod
    def from_dto(cls, dto: TaskOperationOutput) -> TaskOperationResponse:
        """Convert TaskOperationOutput DTO to response model.

        Args:
            dto: TaskOperationOutput from use case

        Returns:
            TaskOperationResponse for API response
        """
        return cls(
            id=dto.id,
            name=dto.name,
            status=dto.status,
            priority=dto.priority,
            deadline=dto.deadline,
            estimated_duration=dto.estimated_duration,
            planned_start=dto.planned_start,
            planned_end=dto.planned_end,
            actual_start=dto.actual_start,
            actual_end=dto.actual_end,
            actual_duration=dto.actual_duration,
            depends_on=dto.depends_on,
            tags=dto.tags,
            is_fixed=dto.is_fixed,
            is_archived=dto.is_archived,
            actual_duration_hours=dto.actual_duration_hours,
        )


class UpdateTaskResponse(BaseModel):
    """Response model for task update operations."""

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
    depends_on: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_fixed: bool = False
    is_archived: bool = False
    actual_duration_hours: float | None = None
    updated_fields: list[str] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: TaskUpdateOutput) -> UpdateTaskResponse:
        """Convert TaskUpdateOutput DTO to response model.

        Args:
            dto: TaskUpdateOutput from use case

        Returns:
            UpdateTaskResponse for API response
        """
        task = dto.task
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
            updated_fields=dto.updated_fields,
        )


class TaskResponse(BaseModel):
    """Response model for task row data (list views)."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    priority: int | None = None
    status: TaskStatus
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    deadline: datetime | None = None
    estimated_duration: float | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    actual_duration_hours: float | None = None
    depends_on: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_fixed: bool = False
    is_archived: bool = False
    is_finished: bool = False
    has_notes: bool = False
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(BaseModel):
    """Response model for detailed task view."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    priority: int | None = None
    status: TaskStatus
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    deadline: datetime | None = None
    estimated_duration: float | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    depends_on: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_fixed: bool = False
    is_archived: bool = False
    daily_allocations: dict[str, float] = Field(default_factory=dict)
    # Computed properties
    actual_duration_hours: float | None = None
    is_active: bool = False
    is_finished: bool = False
    can_be_modified: bool = False
    is_schedulable: bool = False
    has_notes: bool = False
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: TaskDetailOutput) -> TaskDetailResponse:
        """Convert TaskDetailOutput DTO to response model.

        Args:
            dto: TaskDetailOutput from use case

        Returns:
            TaskDetailResponse for API response
        """
        return cls(
            id=dto.task.id,
            name=dto.task.name,
            priority=dto.task.priority,
            status=dto.task.status,
            planned_start=dto.task.planned_start,
            planned_end=dto.task.planned_end,
            deadline=dto.task.deadline,
            estimated_duration=dto.task.estimated_duration,
            actual_start=dto.task.actual_start,
            actual_end=dto.task.actual_end,
            depends_on=dto.task.depends_on,
            tags=dto.task.tags,
            is_fixed=dto.task.is_fixed,
            is_archived=dto.task.is_archived,
            daily_allocations={
                dt.isoformat(): hours
                for dt, hours in dto.task.daily_allocations.items()
            },
            actual_duration_hours=dto.task.actual_duration_hours,
            is_active=dto.task.is_active,
            is_finished=dto.task.is_finished,
            can_be_modified=dto.task.can_be_modified,
            is_schedulable=dto.task.is_schedulable,
            has_notes=dto.has_notes,
            notes=dto.notes_content,
            created_at=dto.task.created_at,
            updated_at=dto.task.updated_at,
        )


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


class GanttTaskResponse(BaseModel):
    """Task data for Gantt chart rendering."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    status: TaskStatus
    estimated_duration: float | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    deadline: datetime | None = None
    daily_allocations: dict[str, float] = Field(default_factory=dict)


class GanttResponse(BaseModel):
    """Response model for Gantt chart data."""

    date_range: GanttDateRange
    tasks: list[GanttTaskResponse]
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
    old_values: dict | None = None
    new_values: dict | None = None
    success: bool
    error_message: str | None = None


class AuditLogListResponse(BaseModel):
    """Response model for audit log list queries."""

    logs: list[AuditLogResponse]
    total_count: int
    limit: int
    offset: int
