"""DTOs for Gantt chart data.

These DTOs provide a presentation-agnostic representation of Gantt chart data,
containing only business data (no presentation logic like colors or styles).
This enables multi-client support (CLI, TUI, Web, API) and future extensibility.

Design Principle:
- Application layer: Returns raw business data (tasks, dates, hours)
- Presentation layer: Decides how to display (colors, styles, layout)
"""

from dataclasses import dataclass
from datetime import date

from domain.entities.task import Task


@dataclass
class GanttDateRange:
    """Date range for the Gantt chart.

    Attributes:
        start_date: Start date of the chart (inclusive)
        end_date: End date of the chart (inclusive)
    """

    start_date: date
    end_date: date

    @property
    def total_days(self) -> int:
        """Calculate total number of days in the range.

        Returns:
            Number of days (inclusive)
        """
        return (self.end_date - self.start_date).days + 1


@dataclass
class GanttOutput:
    """Complete Gantt chart data result.

    This DTO contains only business data needed for Gantt visualization.
    Presentation layers (CLI, TUI, Web) are responsible for:
    - Determining visual representation (colors, styles, symbols)
    - Calculating display flags (is_planned, is_actual, is_deadline)
    - Formatting the data for their specific rendering technology

    Design notes:
    - Contains filtered and sorted tasks
    - Pre-computed daily hour allocations per task
    - Pre-computed daily workload totals
    - Serializable for API responses (REST, gRPC, WebSocket)
    - Language-agnostic structure enables multi-language clients

    Attributes:
        date_range: Date range covered by the chart
        tasks: Filtered and sorted tasks to display
        task_daily_hours: Daily hour allocations per task (task.id -> {date: hours})
        daily_workload: Daily workload totals across all tasks
    """

    date_range: GanttDateRange
    tasks: list[Task]
    task_daily_hours: dict[int, dict[date, float]]
    daily_workload: dict[date, float]

    def is_empty(self) -> bool:
        """Check if the Gantt chart has any task data.

        Returns:
            True if no tasks are present
        """
        return len(self.tasks) == 0
