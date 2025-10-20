"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import ClassVar

from textual.binding import Binding
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
from shared.constants import SATURDAY, SUNDAY
from shared.utils.date_utils import DateTimeParser


class GanttDataTable(DataTable):
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides an interactive Gantt chart with:
    - Vi-style keyboard navigation
    - Task selection and detail viewing
    - Dynamic date range adjustment
    - Workload visualization
    """

    # Vi-style bindings similar to TaskTable
    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the Gantt data table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True

        # Internal state
        self._task_map: dict[int, Task] = {}  # Maps row index to Task
        self._gantt_result: GanttResult | None = None
        self._date_columns: list[date] = []  # Columns representing dates

    def setup_columns(
        self,
        start_date: date,
        end_date: date,
    ):
        """Set up table columns including dynamic date columns.

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

        # Add date columns (3 characters per day: "16 ")
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)

            # Column header shows day number
            day_str = f"{current_date.day}"
            self.add_column(day_str, width=3)

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
            self._task_map[idx + 3] = task  # +3 because of header rows

        # Add workload summary row
        self._add_workload_row(
            gantt_result.daily_workload,
            gantt_result.date_range.start_date,
            gantt_result.date_range.end_date,
        )

    def _add_date_header_rows(self, start_date: date, end_date: date):
        """Add date header rows (Month, Today marker, Day).

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        days = (end_date - start_date).days + 1

        # Build three header rows
        month_row = ["", "[dim]Month[/dim]", ""]
        today_row = ["", "[dim]Today[/dim]", ""]
        day_row = ["", "[dim]Day[/dim]", ""]

        current_month = None
        today = date.today()

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            month = current_date.month
            day = current_date.day
            weekday = current_date.weekday()
            is_today = current_date == today

            # Month row: show month abbreviation when it changes
            if month != current_month:
                month_str = current_date.strftime("%b")
                month_row.append(f"[bold yellow]{month_str}[/bold yellow]")
                current_month = month
            else:
                month_row.append("[dim]   [/dim]")

            # Today marker row
            if is_today:
                today_row.append(f"[bold yellow]{SYMBOL_TODAY}[/bold yellow]")
            else:
                today_row.append("[dim] [/dim]")

            # Day row with weekday coloring
            day_str = f"{day:2d}"
            if weekday == SATURDAY:
                day_style = DAY_STYLE_SATURDAY
            elif weekday == SUNDAY:
                day_style = DAY_STYLE_SUNDAY
            else:
                day_style = DAY_STYLE_WEEKDAY
            day_row.append(f"[{day_style}]{day_str}[/{day_style}]")

        # Add rows to table
        self.add_row(*month_row)
        self.add_row(*today_row)
        self.add_row(*day_row)

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
        # Build row data
        row_data = []

        # Fixed columns
        row_data.append(str(task.id))

        # Task name with strikethrough for completed tasks
        task_name = task.name
        if task.status == TaskStatus.COMPLETED:
            task_name = f"[strike]{task_name}[/strike]"
        row_data.append(task_name)

        # Estimated hours
        if task.estimated_duration:
            row_data.append(f"{task.estimated_duration:.1f}")
        else:
            row_data.append("-")

        # Timeline cells
        days = (end_date - start_date).days + 1
        parsed_dates = self._parse_task_dates(task)

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Format cell
            cell_text = self._format_timeline_cell(
                current_date,
                hours,
                parsed_dates,
                task.status,
            )
            row_data.append(cell_text)

        self.add_row(*row_data)

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
        row_data = []

        # Fixed columns
        row_data.append("")
        row_data.append("[bold yellow]Workload[h][/bold yellow]")
        row_data.append("")

        # Workload cells
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = daily_workload.get(current_date, 0.0)

            # Format with color based on workload level
            import math

            hours_ceiled = math.ceil(hours)

            if hours == 0:
                cell_text = "[dim]-[/dim]"
            elif hours <= 6:  # Comfortable
                cell_text = f"[bold green]{hours_ceiled}[/bold green]"
            elif hours <= 8:  # Moderate
                cell_text = f"[bold yellow]{hours_ceiled}[/bold yellow]"
            else:  # Heavy
                cell_text = f"[bold red]{hours_ceiled}[/bold red]"

            row_data.append(cell_text)

        self.add_row(*row_data)

    def _format_timeline_cell(
        self,
        current_date: date,
        hours: float,
        parsed_dates: dict,
        status: str,
    ) -> str:
        """Format a single timeline cell with styling.

        Args:
            current_date: Date of the cell
            hours: Allocated hours for this date
            parsed_dates: Dictionary of parsed task dates
            status: Task status

        Returns:
            Formatted cell text with Rich markup
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
            if bg_color:
                return f"[{status_color} on {bg_color}]{symbol}[/{status_color} on {bg_color}]"
            else:
                return f"[{status_color}]{symbol}[/{status_color}]"

        # Layer 1: Show hours (for planned or deadline without actual)
        # COMPLETED tasks: hide planned hours
        if hours > 0 and status != TaskStatus.COMPLETED:
            # Format: "4 " or "2.5"
            if hours == int(hours):
                display = f"{int(hours):2d}"
            else:
                display = f"{hours:3.1f}"
        else:
            display = SYMBOL_EMPTY  # "·"

        # Apply background color
        if bg_color:
            return f"[on {bg_color}]{display}[/on {bg_color}]"
        else:
            return f"[dim]{display}[/dim]"

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

    def get_selected_task(self) -> Task | None:
        """Get the currently selected task.

        Returns:
            The selected Task, or None if no task is selected
        """
        if self.cursor_row < 0 or self.cursor_row >= len(self._task_map) + 3:
            return None
        return self._task_map.get(self.cursor_row)

    def action_scroll_home(self) -> None:
        """Move cursor to top (g key)."""
        if self.row_count > 3:  # Skip header rows
            self.move_cursor(row=3)

    def action_scroll_end(self) -> None:
        """Move cursor to bottom (G key)."""
        if self.row_count > 3:
            # Move to last task row (before workload row)
            self.move_cursor(row=self.row_count - 2)

    def action_page_down(self) -> None:
        """Move cursor down by half page (Ctrl+d)."""
        if self.row_count > 3:
            new_row = min(self.cursor_row + 10, self.row_count - 2)
            self.move_cursor(row=new_row)

    def action_page_up(self) -> None:
        """Move cursor up by half page (Ctrl+u)."""
        if self.row_count > 3:
            new_row = max(self.cursor_row - 10, 3)
            self.move_cursor(row=new_row)
