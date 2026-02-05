"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import Any, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable

from taskdog.constants.table_dimensions import TASK_NAME_COLUMN_WIDTH
from taskdog.renderers.gantt_cell_formatter import GanttCellFormatter
from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel

# Constants
GANTT_HEADER_ROW_COUNT = 3  # Number of header rows (Month, Week, Date)


class GanttDataTable(DataTable):  # type: ignore[type-arg]
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides a read-only Gantt chart display with:
    - Dynamic date range adjustment
    - Workload visualization
    - Status-based coloring
    """

    # No bindings - read-only display
    # Note: Base DataTable uses list[Binding | tuple] but list is invariant
    BINDINGS: ClassVar[list[Binding]] = []  # type: ignore[assignment]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Gantt data table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "none"
        self.zebra_stripes = True
        self.can_focus = False

        # Remove cell padding to match CLI spacing (no extra spaces between dates)
        self.styles.padding = (0, 0)

        # Internal state
        self._task_map: dict[
            int, TaskGanttRowViewModel
        ] = {}  # Maps row index to TaskViewModel
        # NOTE: _gantt_view_model removed - data passed as parameter to load_gantt (Step 4)
        self._date_columns: list[date] = []  # Columns representing dates

    def setup_columns(
        self,
        start_date: date,
        end_date: date,
    ) -> None:
        """Set up table columns including Timeline column.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
        """
        # Clear existing columns
        self.clear(columns=True)
        self._date_columns.clear()

        # Add fixed columns with centered headers
        self.add_column(Text("ID", justify="center"))
        self.add_column(Text("Task", justify="center"), width=TASK_NAME_COLUMN_WIDTH)
        self.add_column(Text("Estimated[h]", justify="center"))

        # Add single Timeline column (contains all dates)
        # Store date range for later use
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)

        # Single Timeline column with centered header
        self.add_column(Text("Timeline", justify="center"))

    def load_gantt(
        self, gantt_view_model: GanttViewModel, keep_scroll_position: bool = False
    ) -> None:
        """Load Gantt data into the table.

        Args:
            gantt_view_model: Presentation-ready Gantt data
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        # Save scroll position before refresh (both vertical and horizontal)
        # Note: scroll_y/scroll_x types from DataTable base class (type: ignore needed)
        saved_scroll_y: float | None = (
            self.scroll_y if keep_scroll_position else None  # type: ignore[has-type]
        )
        saved_scroll_x: float | None = (
            self.scroll_x if keep_scroll_position else None  # type: ignore[has-type]
        )

        # NOTE: No longer storing view model locally - just use parameter (Step 4)
        self._task_map.clear()

        # Setup columns based on date range
        self.setup_columns(
            gantt_view_model.start_date,
            gantt_view_model.end_date,
        )

        # Add date header rows (Month, Today marker, Day)
        # Always add these to give Timeline column proper width
        self._add_date_header_rows(
            gantt_view_model.start_date,
            gantt_view_model.end_date,
            gantt_view_model.holidays,
        )

        # Fix the date header rows at the top during vertical scrolling
        # Must be set after rows are added, not in __init__
        self.fixed_rows = GANTT_HEADER_ROW_COUNT

        if gantt_view_model.is_empty():
            return

        # Add task rows
        for idx, task_vm in enumerate(gantt_view_model.tasks):
            task_daily_hours = gantt_view_model.task_daily_hours.get(task_vm.id, {})
            self._add_task_row(
                task_vm,
                task_daily_hours,
                gantt_view_model.start_date,
                gantt_view_model.end_date,
                gantt_view_model.holidays,
            )
            self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

        # Add workload summary row
        self._add_workload_row(
            gantt_view_model.daily_workload,
            gantt_view_model.start_date,
            gantt_view_model.end_date,
            gantt_view_model.total_estimated_duration,
        )

        # Restore scroll position to prevent stuttering
        # Apply bounds check to handle cases where table dimensions changed
        if saved_scroll_y is not None:
            max_scroll_y = max(0, self.virtual_size.height - self.size.height)
            self.scroll_y = min(saved_scroll_y, max_scroll_y)
        if saved_scroll_x is not None:
            max_scroll_x = max(0, self.virtual_size.width - self.size.width)
            self.scroll_x = min(saved_scroll_x, max_scroll_x)

    def _add_date_header_rows(
        self, start_date: date, end_date: date, holidays: set[date]
    ) -> None:
        """Add date header rows (Month, Today marker, Day) as separate rows.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        # Get the three header lines from the formatter
        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, holidays
        )

        # Add three separate rows for month, today marker, and day with centered cells
        self.add_row(
            Text("", justify="center"),
            Text("", justify="center"),
            Text("", justify="center"),
            month_line,
        )
        self.add_row(
            Text("", justify="center"),
            Text("", justify="center"),
            Text("", justify="center"),
            today_line,
        )
        self.add_row(
            Text("", justify="center"),
            Text("", justify="center"),
            Text("", justify="center"),
            day_line,
        )

    def _add_task_row(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ) -> None:
        """Add a task row to the Gantt table.

        Args:
            task_vm: Task ViewModel to add
            task_daily_hours: Daily hours allocation for this task
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        task_id, task_name, est_hours = self._format_task_metadata(task_vm)
        timeline = self._build_timeline(
            task_vm, task_daily_hours, start_date, end_date, holidays
        )

        self.add_row(
            Text(task_id, justify="center"),
            Text.from_markup(task_name, justify="left"),
            Text(est_hours, justify="center"),
            timeline,
        )

    def _format_task_metadata(
        self, task_vm: TaskGanttRowViewModel
    ) -> tuple[str, str, str]:
        """Format fixed column metadata for a task.

        Args:
            task_vm: Task ViewModel to format

        Returns:
            Tuple of (task_id, task_name, estimated_hours)
        """
        # Use pre-formatted values from ViewModel
        task_id = str(task_vm.id)
        task_name = task_vm.formatted_name
        est_hours = task_vm.formatted_estimated_duration

        return task_id, task_name, est_hours

    def _build_timeline(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ) -> Text:
        """Build timeline visualization for a task.

        Args:
            task_vm: Task ViewModel to build timeline for
            task_daily_hours: Daily hours allocation
            start_date: Start date of timeline
            end_date: End date of timeline
            holidays: Set of holiday dates for styling

        Returns:
            Rich Text object with formatted timeline
        """
        days = (end_date - start_date).days + 1

        # Create parsed_dates dict from ViewModel (dates are already converted)
        parsed_dates = {
            "planned_start": task_vm.planned_start,
            "planned_end": task_vm.planned_end,
            "actual_start": task_vm.actual_start,
            "actual_end": task_vm.actual_end,
            "deadline": task_vm.deadline,
        }

        timeline = Text()

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Get formatted cell from formatter
            display, style = GanttCellFormatter.format_timeline_cell(
                current_date,
                hours,
                parsed_dates,
                task_vm.status,
                holidays,
            )
            timeline.append(display, style=style)

        return timeline

    def _add_workload_row(
        self,
        daily_workload: dict[date, float],
        start_date: date,
        end_date: date,
        total_estimated_duration: float = 0.0,
    ) -> None:
        """Add workload summary row.

        Args:
            daily_workload: Pre-computed daily workload totals
            start_date: Start date of the chart
            end_date: End date of the chart
            total_estimated_duration: Sum of all estimated durations
        """
        # Build workload timeline using the formatter
        workload_timeline = GanttCellFormatter.build_workload_timeline(
            daily_workload, start_date, end_date
        )

        # Format total estimated duration
        total_est_str = (
            f"{total_estimated_duration:.1f}" if total_estimated_duration > 0 else "-"
        )

        self.add_row(
            Text("", justify="center"),
            Text("Est. Workload[h]", style="bold yellow", justify="center"),
            Text(total_est_str, style="bold yellow", justify="center"),
            workload_timeline,
        )

    def get_legend_text(self) -> Text:
        """Build legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        return GanttCellFormatter.build_legend()
