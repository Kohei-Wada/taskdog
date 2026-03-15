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

from taskdog.constants.common import HEADER_ESTIMATED, HEADER_ID, HEADER_NAME
from taskdog.constants.gantt import CHARS_PER_DAY, GANTT_WORKLOAD_LABEL
from taskdog.constants.task_table import ESTIMATED_COLUMN_WIDTH, TASK_NAME_COLUMN_WIDTH
from taskdog.renderers.gantt_cell_formatter import GanttCellFormatter
from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog_core.shared.constants import (
    WORKLOAD_COMFORTABLE_HOURS,
    WORKLOAD_MODERATE_HOURS,
)
from taskdog_core.shared.constants.time import DAYS_PER_WEEK

# Constants
GANTT_HEADER_ROW_COUNT = 3  # Number of header rows (Month, Week, Date)


class GanttDataTable(DataTable):  # type: ignore[type-arg]
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides a read-only Gantt chart display with:
    - Dynamic date range adjustment
    - Workload visualization
    - Status-based coloring
    """

    # Vi-style cell navigation bindings
    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        # h/j/k/l -> DataTable built-in cursor movement
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "cursor_left", "Left", show=False),
        Binding("l", "cursor_right", "Right", show=False),
        # g/G -> move cursor to top/bottom row
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False),
        # w/b -> jump by one week (7 columns)
        Binding("w", "cursor_forward_week", "Week Forward", show=False),
        Binding("b", "cursor_backward_week", "Week Backward", show=False),
        # 0/$ -> jump to leftmost/rightmost column
        Binding("0", "cursor_home_horizontal", "Line Start", show=False),
        Binding("$", "cursor_end_horizontal", "Line End", show=False),
        # Ctrl+d/u -> page scroll
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Gantt data table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "cell"
        self.zebra_stripes = True
        self.can_focus = True
        # Remove cell padding so date columns render at exact CHARS_PER_DAY width
        self.cell_padding = 0

        # Remove widget padding
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
        # Pad headers with spaces to compensate for cell_padding=0
        self.add_column(Text(f" {HEADER_ID} ", justify="center"))
        self.add_column(
            Text(f" {HEADER_NAME} ", justify="center"), width=TASK_NAME_COLUMN_WIDTH
        )
        self.add_column(
            Text(f" {HEADER_ESTIMATED} ", justify="center"),
            width=ESTIMATED_COLUMN_WIDTH,
        )

        # Add one column per date
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)
            self.add_column(Text("", justify="center"), width=CHARS_PER_DAY)

    def load_gantt(
        self,
        gantt_view_model: GanttViewModel,
        keep_scroll_position: bool = False,
        comfortable_hours: float = WORKLOAD_COMFORTABLE_HOURS,
        moderate_hours: float = WORKLOAD_MODERATE_HOURS,
    ) -> None:
        """Load Gantt data into the table.

        Args:
            gantt_view_model: Presentation-ready Gantt data
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone
        """
        # Save scroll and cursor position before refresh
        # Note: scroll_y/scroll_x types from DataTable base class (type: ignore needed)
        saved_scroll_y: float | None = (
            self.scroll_y if keep_scroll_position else None  # type: ignore[has-type]
        )
        saved_scroll_x: float | None = (
            self.scroll_x if keep_scroll_position else None  # type: ignore[has-type]
        )
        saved_cursor_row: int | None = self.cursor_row if keep_scroll_position else None
        saved_cursor_col: int | None = (
            self.cursor_column if keep_scroll_position else None
        )

        # NOTE: No longer storing view model locally - just use parameter (Step 4)
        self._task_map.clear()

        # Batch all table mutations to trigger a single layout reflow
        with self.app.batch_update():
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
                comfortable_hours=comfortable_hours,
                moderate_hours=moderate_hours,
            )

        # Restore scroll position to prevent stuttering
        # Apply bounds check to handle cases where table dimensions changed
        if saved_scroll_y is not None:
            max_scroll_y = max(0, self.virtual_size.height - self.size.height)
            self.scroll_y = min(saved_scroll_y, max_scroll_y)
        if saved_scroll_x is not None:
            max_scroll_x = max(0, self.virtual_size.width - self.size.width)
            self.scroll_x = min(saved_scroll_x, max_scroll_x)

        # Restore cursor position with bounds check
        if saved_cursor_row is not None and saved_cursor_col is not None:
            max_row = max(self.row_count - 1, 0)
            max_col = max(len(self.columns) - 1, 0)
            self.move_cursor(
                row=min(saved_cursor_row, max_row),
                column=min(saved_cursor_col, max_col),
            )

    def _add_date_header_rows(
        self, start_date: date, end_date: date, holidays: set[date]
    ) -> None:
        """Add date header rows (Month, Today marker, Day) as separate rows.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        # Get per-date header cells from the formatter
        month_cells, today_cells, day_cells = (
            GanttCellFormatter.build_date_header_cells(start_date, end_date, holidays)
        )

        empty = Text("", justify="center")

        # Add three separate rows for month, today marker, and day
        self.add_row(empty, empty, empty, *month_cells)
        self.add_row(empty, empty, empty, *today_cells)
        self.add_row(empty, empty, empty, *day_cells)

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
        date_cells = self._build_timeline_cells(
            task_vm, task_daily_hours, start_date, end_date, holidays
        )

        self.add_row(
            Text(f" {task_id} ", justify="center"),
            Text.from_markup(f" {task_name} ", justify="left"),
            Text(f" {est_hours} ", justify="center"),
            *date_cells,
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

    def _build_timeline_cells(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ) -> list[Text]:
        """Build timeline cells for a task, one Text per date.

        Args:
            task_vm: Task ViewModel to build timeline for
            task_daily_hours: Daily hours allocation
            start_date: Start date of timeline
            end_date: End date of timeline
            holidays: Set of holiday dates for styling

        Returns:
            List of Rich Text objects, one per date
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

        cells: list[Text] = []

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            display, style = GanttCellFormatter.format_timeline_cell(
                current_date,
                hours,
                parsed_dates,
                task_vm.status,
                holidays,
            )
            cells.append(Text(display, style=style, justify="center"))

        return cells

    def _add_workload_row(
        self,
        daily_workload: dict[date, float],
        start_date: date,
        end_date: date,
        total_estimated_duration: float = 0.0,
        comfortable_hours: float = WORKLOAD_COMFORTABLE_HOURS,
        moderate_hours: float = WORKLOAD_MODERATE_HOURS,
    ) -> None:
        """Add workload summary row.

        Args:
            daily_workload: Pre-computed daily workload totals
            start_date: Start date of the chart
            end_date: End date of the chart
            total_estimated_duration: Sum of all estimated durations
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone
        """
        # Build per-date workload cells using the formatter
        workload_cells = GanttCellFormatter.build_workload_cells(
            daily_workload,
            start_date,
            end_date,
            comfortable_hours=comfortable_hours,
            moderate_hours=moderate_hours,
        )

        # Format total estimated duration
        total_est_str = (
            f"{total_estimated_duration:.1f}" if total_estimated_duration > 0 else "-"
        )

        self.add_row(
            Text("", justify="center"),
            Text(f" {GANTT_WORKLOAD_LABEL} ", style="bold yellow", justify="center"),
            Text(f" {total_est_str} ", style="bold yellow", justify="center"),
            *workload_cells,
        )

    def action_cursor_top(self) -> None:
        """Move cursor to the first row (g key)."""
        self.move_cursor(row=0)

    def action_cursor_bottom(self) -> None:
        """Move cursor to the last row (G key)."""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)

    def action_cursor_forward_week(self) -> None:
        """Move cursor forward by one week (w key)."""
        new_col = min(self.cursor_column + DAYS_PER_WEEK, len(self.columns) - 1)
        self.move_cursor(column=new_col)

    def action_cursor_backward_week(self) -> None:
        """Move cursor backward by one week (b key)."""
        new_col = max(self.cursor_column - DAYS_PER_WEEK, 0)
        self.move_cursor(column=new_col)

    def action_cursor_home_horizontal(self) -> None:
        """Move cursor to the first column (0 key)."""
        self.move_cursor(column=0)

    def action_cursor_end_horizontal(self) -> None:
        """Move cursor to the last column ($ key)."""
        if self.columns:
            self.move_cursor(column=len(self.columns) - 1)

    def get_selected_task_id(self) -> int | None:
        """Get the task ID at the current cursor row.

        Returns:
            Task ID if cursor is on a task row, None if on header/workload row.
        """
        task_vm = self._task_map.get(self.cursor_row)
        return task_vm.id if task_vm else None

    def get_selected_task_vm(self) -> TaskGanttRowViewModel | None:
        """Get the TaskGanttRowViewModel at the current cursor row.

        Returns:
            TaskGanttRowViewModel if cursor is on a task row, None otherwise.
        """
        return self._task_map.get(self.cursor_row)

    def get_legend_text(self) -> Text:
        """Build legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        return GanttCellFormatter.build_legend()
