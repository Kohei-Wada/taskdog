"""DTOs for Gantt chart data.

The Gantt overlay carries only the data that is unique to the Gantt view
(daily allocations, workload totals, holidays, date range). Task data itself
is shared with the table via the canonical ``TaskRowDto`` list and joined by
task id, so the overlay never duplicates task fields.

Design Principle:
- Application layer: Returns raw business data (allocations, workload, dates)
- Presentation layer: Decides how to display (colors, styles, layout)
"""

from datetime import date

from pydantic import BaseModel


class GanttDateRange(BaseModel):
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


class GanttOverlay(BaseModel):
    """Gantt-specific overlay data, joined to the shared task list by id.

    This DTO contains only the business data that is unique to the Gantt view.
    Task fields (name, status, dates, ...) are not duplicated here; consumers
    join this overlay with the shared ``TaskRowDto`` list using ``task.id``.

    Presentation layers (CLI, TUI, Web) are responsible for:
    - Determining visual representation (colors, styles, symbols)
    - Calculating display flags (is_planned, is_actual, is_deadline)
    - Formatting the data for their specific rendering technology

    Attributes:
        date_range: Date range covered by the chart
        task_daily_hours: Daily hour allocations per task (task.id -> {date: hours})
        daily_workload: Daily workload totals across all tasks
        holidays: Set of holiday dates in the chart range
        total_estimated_duration: Sum of all estimated durations in hours
    """

    date_range: GanttDateRange
    task_daily_hours: dict[int, dict[date, float]]
    daily_workload: dict[date, float]
    holidays: set[date]
    total_estimated_duration: float = 0.0
