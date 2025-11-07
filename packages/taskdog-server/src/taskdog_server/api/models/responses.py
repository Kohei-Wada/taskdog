"""Pydantic response models for FastAPI endpoints."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from taskdog_core.domain.entities.task import TaskStatus


class TaskOperationResponse(BaseModel):
    """Response model for task write operations (create, update, status changes)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: TaskStatus
    priority: int
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
    actual_daily_hours: dict[str, float] = Field(default_factory=dict)


class UpdateTaskResponse(BaseModel):
    """Response model for task update operations."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: TaskStatus
    priority: int
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
    actual_daily_hours: dict[str, float] = Field(default_factory=dict)
    updated_fields: list[str] = Field(default_factory=list)


class TaskResponse(BaseModel):
    """Response model for task row data (list views)."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: int
    name: str
    priority: int
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
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(BaseModel):
    """Response model for detailed task view."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: int
    name: str
    priority: int
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
    actual_daily_hours: dict[str, float] = Field(default_factory=dict)
    # Computed properties
    actual_duration_hours: float | None = None
    is_active: bool = False
    is_finished: bool = False
    can_be_modified: bool = False
    is_schedulable: bool = False
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Response model for task list queries."""

    tasks: list[TaskResponse]
    total_count: int
    filtered_count: int
    gantt: "GanttResponse | None" = None


class GanttDateRange(BaseModel):
    """Date range for Gantt chart."""

    start_date: date
    end_date: date


class GanttTaskResponse(BaseModel):
    """Task data for Gantt chart rendering."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: int
    name: str
    status: TaskStatus
    estimated_duration: float | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    deadline: datetime | None = None
    is_fixed: bool = False
    is_archived: bool = False
    daily_allocations: dict[str, float] = Field(default_factory=dict)


class GanttResponse(BaseModel):
    """Response model for Gantt chart data."""

    date_range: GanttDateRange
    tasks: list[GanttTaskResponse]
    task_daily_hours: dict[int, dict[str, float]]
    daily_workload: dict[str, float]
    holidays: list[str] = Field(default_factory=list)


class CompletionStatistics(BaseModel):
    """Completion rate statistics."""

    total: int
    completed: int
    in_progress: int
    pending: int
    canceled: int
    completion_rate: float


class TimeStatistics(BaseModel):
    """Time tracking statistics."""

    total_logged_hours: float
    average_task_duration: float | None = None
    total_estimated_hours: float


class EstimationStatistics(BaseModel):
    """Estimation accuracy statistics."""

    average_deviation: float
    average_deviation_percentage: float
    tasks_with_estimates: int


class DeadlineStatistics(BaseModel):
    """Deadline adherence statistics."""

    met: int
    missed: int
    no_deadline: int
    adherence_rate: float


class PriorityDistribution(BaseModel):
    """Task distribution by priority."""

    distribution: dict[int, int]


class TrendData(BaseModel):
    """Trend data over time."""

    completed_per_day: dict[str, int]
    hours_per_day: dict[str, float]


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
