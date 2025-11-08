"""ViewModels for Gantt chart presentation.

These ViewModels contain only the data needed for rendering Gantt charts,
without domain entity references. All presentation logic (formatting,
strikethrough, etc.) is applied by the Mapper before creating these ViewModels.
"""

from dataclasses import dataclass
from datetime import date

from taskdog.view_models.base import BaseViewModel
from taskdog_core.domain.entities.task import TaskStatus


@dataclass(frozen=True)
class TaskGanttRowViewModel(BaseViewModel):
    """ViewModel for a single task row in the Gantt chart.

    This contains all data needed to render a task in the Gantt chart,
    with presentation logic already applied (e.g., strikethrough for finished tasks).

    Attributes:
        id: Task ID
        name: Task name (raw, without formatting)
        formatted_name: Task name with presentation formatting (strikethrough, etc.)
        estimated_duration: Estimated duration in hours (None if not set)
        formatted_estimated_duration: Formatted duration string (e.g., "8.0", "-")
        status: Task status (needed for timeline cell formatting)
        planned_start: Planned start date (None if not set)
        planned_end: Planned end date (None if not set)
        actual_start: Actual start date (None if not set)
        actual_end: Actual end date (None if not set)
        deadline: Deadline date (None if not set)
        is_finished: Whether task is in a finished state (COMPLETED/CANCELED)
    """

    id: int
    name: str
    formatted_name: str
    estimated_duration: float | None
    formatted_estimated_duration: str
    status: TaskStatus
    planned_start: date | None
    planned_end: date | None
    actual_start: date | None
    actual_end: date | None
    deadline: date | None
    is_finished: bool


@dataclass(frozen=True)
class GanttViewModel(BaseViewModel):
    """ViewModel for complete Gantt chart data.

    This is the presentation-ready version of GanttOutput, containing
    TaskGanttRowViewModel instead of Task entities.

    Attributes:
        start_date: Start date of the chart
        end_date: End date of the chart
        tasks: List of task view models for display
        task_daily_hours: Daily hour allocations per task (task.id -> {date: hours})
        daily_workload: Daily workload totals across all tasks
        holidays: Set of holiday dates in the chart range (for rendering)
    """

    start_date: date
    end_date: date
    tasks: list[TaskGanttRowViewModel]
    task_daily_hours: dict[int, dict[date, float]]
    daily_workload: dict[date, float]
    holidays: set[date]

    @property
    def total_days(self) -> int:
        """Calculate total number of days in the chart range.

        Returns:
            Number of days (inclusive)
        """
        return (self.end_date - self.start_date).days + 1

    def is_empty(self) -> bool:
        """Check if the Gantt chart has any task data.

        Returns:
            True if no tasks are present
        """
        return len(self.tasks) == 0
