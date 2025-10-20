"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import ClassVar

from rich.text import Text
from textual.widgets import DataTable

from application.dto.gantt_result import GanttResult
from domain.entities.task import Task, TaskStatus
from presentation.constants.colors import (
    DAY_STYLE_SATURDAY,
    DAY_STYLE_SUNDAY,
    DAY_STYLE_WEEKDAY,
)
from presentation.constants.symbols import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_DEADLINE,
    BACKGROUND_COLOR_SATURDAY,
    BACKGROUND_COLOR_SUNDAY,
    SYMBOL_ACTUAL,
    SYMBOL_EMPTY,
    SYMBOL_TODAY,
)
from presentation.constants.table_dimensions import (
    GANTT_TABLE_EST_HOURS_WIDTH,
    GANTT_TABLE_ID_WIDTH,
    GANTT_TABLE_TASK_MIN_WIDTH,
)
from shared.constants import (
    SATURDAY,
    SUNDAY,
    WORKLOAD_COMFORTABLE_HOURS,
    WORKLOAD_MODERATE_HOURS,
)
from shared.utils.date_utils import DateTimeParser


class GanttDataTable(DataTable):
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides a read-only Gantt chart display with:
    - Dynamic date range adjustment
    - Workload visualization
    - Status-based coloring
    """

    # No bindings - read-only display
    BINDINGS: ClassVar = []

    def __init__(self, *args, **kwargs):
        """Initialize the Gantt data table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "none"
        self.zebra_stripes = True
        self.can_focus = False

        # Remove cell padding to match CLI spacing (no extra spaces between dates)
        self.styles.padding = (0, 0)

        # Internal state
        self._task_map: dict[int, Task] = {}  # Maps row index to Task
        self._gantt_result: GanttResult | None = None
        self._date_columns: list[date] = []  # Columns representing dates

    def setup_columns(
        self,
        start_date: date,
        end_date: date,
    ):
        """Set up table columns including Timeline column.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        # Clear existing columns
        self.clear(columns=True)
        self._date_columns.clear()

        # Add fixed columns
        self.add_column("ID", width=GANTT_TABLE_ID_WIDTH)
        self.add_column("Task", width=GANTT_TABLE_TASK_MIN_WIDTH)
        self.add_column("Est[h]", width=GANTT_TABLE_EST_HOURS_WIDTH)

        # Add single Timeline column (contains all dates)
        # Store date range for later use
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)

        # Single Timeline column
        self.add_column("Timeline")

    def load_gantt(self, gantt_result: GanttResult):
        """Load Gantt data into the table.

        Args:
            gantt_result: Pre-computed Gantt data from Application layer
        """
        self._gantt_result = gantt_result
        self._task_map.clear()

        # Setup columns based on date range
        self.setup_columns(
            gantt_result.date_range.start_date,
            gantt_result.date_range.end_date,
        )

        if gantt_result.is_empty():
            return

        # Add date header rows (Month, Today marker, Day)
        self._add_date_header_rows(
            gantt_result.date_range.start_date,
            gantt_result.date_range.end_date,
        )

        # Add task rows
        for idx, task in enumerate(gantt_result.tasks):
            task_daily_hours = gantt_result.task_daily_hours.get(task.id, {})
            self._add_task_row(
                task,
                task_daily_hours,
                gantt_result.date_range.start_date,
                gantt_result.date_range.end_date,
            )
            self._task_map[idx + 3] = task  # +3 because of 3 header rows

        # Add workload summary row
        self._add_workload_row(
            gantt_result.daily_workload,
            gantt_result.date_range.start_date,
            gantt_result.date_range.end_date,
        )

    def _add_date_header_rows(self, start_date: date, end_date: date):
        """Add date header rows (Month, Today marker, Day) as separate rows.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        days = (end_date - start_date).days + 1

        # Build each line as Rich Text for proper width calculation
        month_line = Text()
        today_line = Text()
        day_line = Text()

        current_month = None
        today = date.today()

        # Build each line separately
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            month = current_date.month
            day = current_date.day
            weekday = current_date.weekday()
            is_today = current_date == today

            # Month line: show month abbreviation when it changes
            if month != current_month:
                month_str = current_date.strftime("%b")
                month_line.append(month_str, style="bold yellow")
                current_month = month
            else:
                month_line.append("   ", style="dim")

            # Today marker line
            if is_today:
                today_line.append(f" {SYMBOL_TODAY} ", style="bold yellow")
            else:
                today_line.append("   ", style="dim")

            # Day line with consistent spacing
            day_str = f"{day:2d} "
            if weekday == SATURDAY:
                day_style = DAY_STYLE_SATURDAY
            elif weekday == SUNDAY:
                day_style = DAY_STYLE_SUNDAY
            else:
                day_style = DAY_STYLE_WEEKDAY
            day_line.append(day_str, style=day_style)

        # Add three separate rows for month, today marker, and day
        self.add_row("", "[dim]Date[/dim]", "", month_line)
        self.add_row("", "", "", today_line)
        self.add_row("", "", "", day_line)

    def _add_task_row(
        self,
        task: Task,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
    ):
        """Add a task row to the Gantt table.

        Args:
            task: Task to add
            task_daily_hours: Daily hours allocation for this task
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        # Fixed columns
        task_id = str(task.id)

        # Task name with strikethrough for completed tasks
        task_name = task.name
        if task.status == TaskStatus.COMPLETED:
            task_name = f"[strike]{task_name}[/strike]"

        # Estimated hours
        est_hours = f"{task.estimated_duration:.1f}" if task.estimated_duration else "-"

        # Build timeline as Rich Text object
        days = (end_date - start_date).days + 1
        parsed_dates = self._parse_task_dates(task)
        timeline = Text()

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Add formatted cell to timeline Text object
            self._append_timeline_cell(
                timeline,
                current_date,
                hours,
                parsed_dates,
                task.status,
            )

        self.add_row(task_id, task_name, est_hours, timeline)

    def _add_workload_row(
        self,
        daily_workload: dict[date, float],
        start_date: date,
        end_date: date,
    ):
        """Add workload summary row.

        Args:
            daily_workload: Pre-computed daily workload totals
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        import math

        # Fixed columns
        workload_id = ""
        workload_label = "[bold yellow]Workload[h][/bold yellow]"
        workload_est = ""

        # Build workload timeline as Rich Text object
        days = (end_date - start_date).days + 1
        workload_timeline = Text()

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = daily_workload.get(current_date, 0.0)
            hours_ceiled = math.ceil(hours)

            # Format as 3-character right-aligned string (e.g., "  0", "  3")
            cell_text = f"{hours_ceiled:2d} "

            if hours == 0:
                workload_timeline.append(cell_text)
            elif hours <= WORKLOAD_COMFORTABLE_HOURS:  # Comfortable (6.0)
                workload_timeline.append(cell_text, style="bold green")
            elif hours <= WORKLOAD_MODERATE_HOURS:  # Moderate (8.0)
                workload_timeline.append(cell_text, style="bold yellow")
            else:  # Heavy (>8.0)
                workload_timeline.append(cell_text, style="bold red")

        self.add_row(workload_id, workload_label, workload_est, workload_timeline)

    def _append_timeline_cell(
        self,
        timeline: Text,
        current_date: date,
        hours: float,
        parsed_dates: dict,
        status: str,
    ):
        """Append a single timeline cell to the Text object.

        Args:
            timeline: Text object to append to
            current_date: Date of the cell
            hours: Allocated hours for this date
            parsed_dates: Dictionary of parsed task dates
            status: Task status
        """
        # Check if date is in special periods
        is_planned = self._is_in_date_range(
            current_date,
            parsed_dates["planned_start"],
            parsed_dates["planned_end"],
        )

        # For actual period: if actual_end is None (IN_PROGRESS),
        # treat actual_start to today as actual period
        if parsed_dates["actual_start"] and not parsed_dates["actual_end"]:
            today = date.today()
            is_actual = parsed_dates["actual_start"] <= current_date <= today
        else:
            is_actual = self._is_in_date_range(
                current_date,
                parsed_dates["actual_start"],
                parsed_dates["actual_end"],
            )

        is_deadline = parsed_dates["deadline"] and current_date == parsed_dates["deadline"]

        # Determine background color
        if is_deadline:
            bg_color = BACKGROUND_COLOR_DEADLINE
        elif is_planned and status != TaskStatus.COMPLETED:
            bg_color = self._get_background_color(current_date)
        else:
            bg_color = None

        # Layer 2: Actual period (highest priority) - use symbol
        if is_actual:
            symbol = SYMBOL_ACTUAL
            status_color = self._get_status_color(status)
            # Append with proper styling: " ◆ " (3 display chars)
            display = f" {symbol} "
            if bg_color:
                timeline.append(display, style=f"{status_color} on {bg_color}")
            else:
                timeline.append(display, style=status_color)
            return

        # Layer 1: Show hours (for planned or deadline without actual)
        # COMPLETED tasks: hide planned hours
        if hours > 0 and status != TaskStatus.COMPLETED:
            # Format as 3 characters, right-aligned (e.g., "  3", "2.5")
            display = f"{int(hours):2d} " if hours == int(hours) else f"{hours:3.1f}"
        else:
            # Use SYMBOL_EMPTY which is already " · " (3 chars)
            display = SYMBOL_EMPTY

        # Apply background color
        if bg_color:
            timeline.append(display, style=f"on {bg_color}")
        else:
            timeline.append(display, style="dim")

    def _parse_task_dates(self, task: Task) -> dict:
        """Parse all task dates into a dictionary.

        Args:
            task: Task to parse dates from

        Returns:
            Dictionary with parsed dates
        """
        return {
            "planned_start": DateTimeParser.parse_date(task.planned_start),
            "planned_end": DateTimeParser.parse_date(task.planned_end),
            "actual_start": DateTimeParser.parse_date(task.actual_start),
            "actual_end": DateTimeParser.parse_date(task.actual_end),
            "deadline": DateTimeParser.parse_date(task.deadline),
        }

    def _is_in_date_range(
        self,
        current_date: date,
        start: date | None,
        end: date | None,
    ) -> bool:
        """Check if a date is within a range.

        Args:
            current_date: Date to check
            start: Start of range (inclusive)
            end: End of range (inclusive)

        Returns:
            True if current_date is within range
        """
        if start and end:
            return start <= current_date <= end
        return False

    def _get_background_color(self, current_date: date) -> str:
        """Get background color based on day of week.

        Args:
            current_date: Date to check

        Returns:
            Background color string (RGB)
        """
        weekday = current_date.weekday()
        if weekday == SATURDAY:
            return BACKGROUND_COLOR_SATURDAY
        elif weekday == SUNDAY:
            return BACKGROUND_COLOR_SUNDAY
        else:
            return BACKGROUND_COLOR

    def _get_status_color(self, status: str) -> str:
        """Get color for task status.

        Args:
            status: Task status

        Returns:
            Color string
        """
        if status == TaskStatus.COMPLETED:
            return "bold green"
        elif status == TaskStatus.IN_PROGRESS:
            return "bold blue"
        elif status == TaskStatus.CANCELED:
            return "dim"
        else:  # PENDING
            return "white"

    def get_legend_text(self) -> str:
        """Build legend text for the Gantt chart.

        Returns:
            Rich-formatted legend text
        """
        legend_parts = [
            "[bold yellow]Legend:[/bold yellow]",
            f"[on {BACKGROUND_COLOR}]   [/on {BACKGROUND_COLOR}] Planned",
            f"[bold blue]{SYMBOL_ACTUAL}[/bold blue] Actual (IN_PROGRESS)",
            f"[bold green]{SYMBOL_ACTUAL}[/bold green] Actual (COMPLETED)",
            f"[on {BACKGROUND_COLOR_DEADLINE}]   [/on {BACKGROUND_COLOR_DEADLINE}] Deadline",
            f"[bold yellow]{SYMBOL_TODAY}[/bold yellow] Today",
            f"[on {BACKGROUND_COLOR_SATURDAY}]   [/on {BACKGROUND_COLOR_SATURDAY}] Saturday",
            f"[on {BACKGROUND_COLOR_SUNDAY}]   [/on {BACKGROUND_COLOR_SUNDAY}] Sunday",
        ]
        return "  ".join(legend_parts)
