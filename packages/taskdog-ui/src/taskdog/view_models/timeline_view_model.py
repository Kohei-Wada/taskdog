"""ViewModels for Timeline (daily time-based Gantt) presentation.

These ViewModels contain only the data needed for rendering the Timeline chart,
which shows actual_start/actual_end times for a specific day on a horizontal time axis.
"""

from dataclasses import dataclass
from datetime import date, time

from taskdog.view_models.base import BaseViewModel
from taskdog_core.domain.entities.task import TaskStatus


@dataclass(frozen=True)
class TimelineTaskRowViewModel(BaseViewModel):
    """ViewModel for a single task row in the Timeline chart.

    This contains all data needed to render a task in the Timeline chart,
    with presentation logic already applied (e.g., strikethrough for finished tasks).

    Attributes:
        task_id: Task ID
        name: Task name (raw, without formatting)
        formatted_name: Task name with presentation formatting (strikethrough, etc.)
        actual_start: Actual start time on the target date
        actual_end: Actual end time on the target date
        duration_hours: Work duration in hours for this date
        status: Task status (needed for bar coloring)
        is_finished: Whether task is in a finished state (COMPLETED/CANCELED)
    """

    task_id: int
    name: str
    formatted_name: str
    actual_start: time
    actual_end: time
    duration_hours: float
    status: TaskStatus
    is_finished: bool


@dataclass(frozen=True)
class TimelineViewModel(BaseViewModel):
    """ViewModel for complete Timeline chart data.

    This is the presentation-ready data for displaying a day's work timeline.

    Attributes:
        target_date: The date being displayed
        rows: List of task row view models for display
        start_hour: Display start hour (e.g., 8 for 08:00)
        end_hour: Display end hour (e.g., 18 for 18:00)
        total_work_hours: Total hours worked on this day
        task_count: Number of tasks with work on this day
    """

    target_date: date
    rows: list[TimelineTaskRowViewModel]
    start_hour: int
    end_hour: int
    total_work_hours: float
    task_count: int

    def is_empty(self) -> bool:
        """Check if the Timeline chart has any task data.

        Returns:
            True if no tasks are present
        """
        return len(self.rows) == 0
