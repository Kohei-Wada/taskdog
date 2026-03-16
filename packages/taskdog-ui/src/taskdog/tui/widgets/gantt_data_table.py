"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import Any, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.widgets import DataTable

from taskdog.constants.common import HEADER_ESTIMATED, HEADER_ID, HEADER_NAME
from taskdog.constants.gantt import CHARS_PER_DAY, GANTT_WORKLOAD_LABEL
from taskdog.constants.task_table import ESTIMATED_COLUMN_WIDTH, TASK_NAME_COLUMN_WIDTH
from taskdog.renderers.gantt_cell_formatter import DateMetadata, GanttCellFormatter
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
        self._date_columns: list[date] = []  # Columns representing dates
        self._prev_date_range: tuple[date, date] | None = None  # For diff detection

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

        Uses a 2-pass rendering strategy:
        - Fast path: when date range is unchanged, updates cells in-place
          via update_cell_at() to preserve cursor/hover state.
        - Full rebuild: when date range changes or on first load, clears
          and reconstructs the entire table.

        Args:
            gantt_view_model: Presentation-ready Gantt data
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone
        """
        new_range = (gantt_view_model.start_date, gantt_view_model.end_date)
        can_diff = (
            self._prev_date_range is not None and self._prev_date_range == new_range
        )

        if can_diff:
            self._differential_update(
                gantt_view_model,
                comfortable_hours=comfortable_hours,
                moderate_hours=moderate_hours,
            )
        else:
            self._full_rebuild(
                gantt_view_model,
                keep_scroll_position=keep_scroll_position,
                comfortable_hours=comfortable_hours,
                moderate_hours=moderate_hours,
            )

        self._prev_date_range = new_range

    def reset_diff_state(self) -> None:
        """Reset differential rendering state.

        Forces the next load_gantt() call to perform a full rebuild.
        Call this when the table is cleared for error/empty messages.
        """
        self._prev_date_range = None

    def _full_rebuild(
        self,
        gantt_view_model: GanttViewModel,
        keep_scroll_position: bool = False,
        comfortable_hours: float = WORKLOAD_COMFORTABLE_HOURS,
        moderate_hours: float = WORKLOAD_MODERATE_HOURS,
    ) -> None:
        """Full table rebuild — clears all columns/rows and reconstructs.

        Used on first load or when the date range changes.

        Args:
            gantt_view_model: Presentation-ready Gantt data
            keep_scroll_position: Whether to preserve scroll position
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone
        """
        # Save scroll and cursor position before refresh
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

        self._task_map.clear()

        # Batch all table mutations to trigger a single layout reflow
        with self.app.batch_update():
            # Setup columns based on date range
            self.setup_columns(
                gantt_view_model.start_date,
                gantt_view_model.end_date,
            )

            # Add date header rows (Month, Today marker, Day)
            header_cells = self._build_header_row_cells(
                gantt_view_model.start_date,
                gantt_view_model.end_date,
                gantt_view_model.holidays,
            )
            empty = Text("", justify="center")
            for row_cells in header_cells:
                self.add_row(empty, empty, empty, *row_cells)

            # Fix the date header rows at the top during vertical scrolling
            self.fixed_rows = GANTT_HEADER_ROW_COUNT

            if gantt_view_model.is_empty():
                return

            # Pre-compute shared date metadata (once for all tasks)
            today = date.today()
            date_metadata = GanttCellFormatter.precompute_date_metadata(
                self._date_columns, gantt_view_model.holidays, today
            )

            # Add task rows
            for idx, task_vm in enumerate(gantt_view_model.tasks):
                task_daily_hours = gantt_view_model.task_daily_hours.get(task_vm.id, {})
                cells = self._build_task_row_cells(
                    task_vm, task_daily_hours, self._date_columns, date_metadata, today
                )
                self.add_row(*cells)
                self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

            # Add workload summary row
            workload_cells = self._build_workload_row_cells(
                gantt_view_model.daily_workload,
                gantt_view_model.start_date,
                gantt_view_model.end_date,
                gantt_view_model.total_estimated_duration,
                comfortable_hours=comfortable_hours,
                moderate_hours=moderate_hours,
            )
            self.add_row(*workload_cells)

        # Restore scroll position to prevent stuttering
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

    def _differential_update(
        self,
        gantt_view_model: GanttViewModel,
        comfortable_hours: float = WORKLOAD_COMFORTABLE_HOURS,
        moderate_hours: float = WORKLOAD_MODERATE_HOURS,
    ) -> None:
        """In-place cell update — preserves cursor/scroll state automatically.

        Row layout: rows 0-2 = headers, rows 3..3+N-1 = tasks, row 3+N = workload.

        Args:
            gantt_view_model: Presentation-ready Gantt data
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone
        """
        self._task_map.clear()

        with self.app.batch_update():
            # 1. Update header rows in-place (today marker may change)
            header_rows = self._build_header_row_cells(
                gantt_view_model.start_date,
                gantt_view_model.end_date,
                gantt_view_model.holidays,
            )
            empty = Text("", justify="center")
            for row_idx, row_cells in enumerate(header_rows):
                self._update_cells_in_place(row_idx, [empty, empty, empty, *row_cells])

            # 2. Compute new task cells
            today = date.today()
            date_metadata = GanttCellFormatter.precompute_date_metadata(
                self._date_columns, gantt_view_model.holidays, today
            )

            new_task_count = len(gantt_view_model.tasks)
            # Previous task count = total rows - headers - workload
            prev_total_rows = self.row_count
            prev_task_count = max(prev_total_rows - GANTT_HEADER_ROW_COUNT - 1, 0)

            if new_task_count == prev_task_count:
                # Same count: update all task rows + workload in-place
                for idx, task_vm in enumerate(gantt_view_model.tasks):
                    task_daily_hours = gantt_view_model.task_daily_hours.get(
                        task_vm.id, {}
                    )
                    cells = self._build_task_row_cells(
                        task_vm,
                        task_daily_hours,
                        self._date_columns,
                        date_metadata,
                        today,
                    )
                    self._update_cells_in_place(GANTT_HEADER_ROW_COUNT + idx, cells)
                    self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

                # Update workload row in-place
                workload_cells = self._build_workload_row_cells(
                    gantt_view_model.daily_workload,
                    gantt_view_model.start_date,
                    gantt_view_model.end_date,
                    gantt_view_model.total_estimated_duration,
                    comfortable_hours=comfortable_hours,
                    moderate_hours=moderate_hours,
                )
                self._update_cells_in_place(
                    GANTT_HEADER_ROW_COUNT + new_task_count, workload_cells
                )

            elif new_task_count > prev_task_count:
                # More tasks: remove old workload row, update existing tasks,
                # add new task rows, then add new workload row
                if prev_task_count > 0:
                    # Remove old workload row
                    workload_row_idx = GANTT_HEADER_ROW_COUNT + prev_task_count
                    row_key, _ = self.coordinate_to_cell_key(
                        Coordinate(workload_row_idx, 0)
                    )
                    self.remove_row(row_key)

                # Update existing task rows
                for idx in range(prev_task_count):
                    task_vm = gantt_view_model.tasks[idx]
                    task_daily_hours = gantt_view_model.task_daily_hours.get(
                        task_vm.id, {}
                    )
                    cells = self._build_task_row_cells(
                        task_vm,
                        task_daily_hours,
                        self._date_columns,
                        date_metadata,
                        today,
                    )
                    self._update_cells_in_place(GANTT_HEADER_ROW_COUNT + idx, cells)
                    self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

                # Add new task rows
                for idx in range(prev_task_count, new_task_count):
                    task_vm = gantt_view_model.tasks[idx]
                    task_daily_hours = gantt_view_model.task_daily_hours.get(
                        task_vm.id, {}
                    )
                    cells = self._build_task_row_cells(
                        task_vm,
                        task_daily_hours,
                        self._date_columns,
                        date_metadata,
                        today,
                    )
                    self.add_row(*cells)
                    self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

                # Add new workload row
                workload_cells = self._build_workload_row_cells(
                    gantt_view_model.daily_workload,
                    gantt_view_model.start_date,
                    gantt_view_model.end_date,
                    gantt_view_model.total_estimated_duration,
                    comfortable_hours=comfortable_hours,
                    moderate_hours=moderate_hours,
                )
                self.add_row(*workload_cells)

            else:
                # Fewer tasks: update remaining task rows, remove excess + old workload,
                # then add new workload row
                for idx in range(new_task_count):
                    task_vm = gantt_view_model.tasks[idx]
                    task_daily_hours = gantt_view_model.task_daily_hours.get(
                        task_vm.id, {}
                    )
                    cells = self._build_task_row_cells(
                        task_vm,
                        task_daily_hours,
                        self._date_columns,
                        date_metadata,
                        today,
                    )
                    self._update_cells_in_place(GANTT_HEADER_ROW_COUNT + idx, cells)
                    self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task_vm

                # Remove excess task rows + old workload row (from end)
                rows_to_remove = (
                    prev_task_count - new_task_count
                ) + 1  # +1 for workload
                for _ in range(rows_to_remove):
                    last_row_idx = self.row_count - 1
                    row_key, _ = self.coordinate_to_cell_key(
                        Coordinate(last_row_idx, 0)
                    )
                    self.remove_row(row_key)

                # Add new workload row
                workload_cells = self._build_workload_row_cells(
                    gantt_view_model.daily_workload,
                    gantt_view_model.start_date,
                    gantt_view_model.end_date,
                    gantt_view_model.total_estimated_duration,
                    comfortable_hours=comfortable_hours,
                    moderate_hours=moderate_hours,
                )
                self.add_row(*workload_cells)

    def _update_cells_in_place(self, row_idx: int, cells: list[Text]) -> None:
        """Update all cells in a row using update_cell_at().

        Args:
            row_idx: Row index to update
            cells: List of Text values, one per column
        """
        for col_idx, value in enumerate(cells):
            self.update_cell_at(Coordinate(row_idx, col_idx), value)

    def _build_header_row_cells(
        self, start_date: date, end_date: date, holidays: set[date]
    ) -> tuple[list[Text], list[Text], list[Text]]:
        """Build date header cells (Month, Today marker, Day).

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling

        Returns:
            Tuple of (month_cells, today_cells, day_cells) lists
        """
        return GanttCellFormatter.build_date_header_cells(
            start_date, end_date, holidays
        )

    def _build_task_row_cells(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        dates: list[date],
        date_metadata: list[DateMetadata],
        today: date,
    ) -> list[Text]:
        """Build all cells for a task row.

        Args:
            task_vm: Task ViewModel
            task_daily_hours: Daily hours allocation for this task
            dates: Pre-computed list of dates in the timeline
            date_metadata: Pre-computed metadata for each date
            today: Current date

        Returns:
            List of Text cells: [ID, Name, Est, *date_cells]
        """
        task_id, task_name, est_hours = self._format_task_metadata(task_vm)
        date_cells = self._build_timeline_cells(
            task_vm, task_daily_hours, dates, date_metadata, today
        )

        return [
            Text(f" {task_id} ", justify="center"),
            Text.from_markup(f" {task_name} ", justify="left"),
            Text(f" {est_hours} ", justify="center"),
            *date_cells,
        ]

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
        dates: list[date],
        date_metadata: list[DateMetadata],
        today: date,
    ) -> list[Text]:
        """Build timeline cells for a task, one Text per date.

        Uses the batch formatter to avoid redundant per-cell computations.

        Args:
            task_vm: Task ViewModel to build timeline for
            task_daily_hours: Daily hours allocation
            dates: Pre-computed list of dates in the timeline
            date_metadata: Pre-computed metadata for each date
            today: Current date (computed once by caller)

        Returns:
            List of Rich Text objects, one per date
        """
        cell_data = GanttCellFormatter.format_timeline_cells_batch(
            dates,
            date_metadata,
            task_daily_hours,
            task_vm.status,
            task_vm.planned_start,
            task_vm.planned_end,
            task_vm.actual_start,
            task_vm.actual_end,
            task_vm.deadline,
            today,
        )

        return [
            Text(display, style=style, justify="center") for display, style in cell_data
        ]

    def _build_workload_row_cells(
        self,
        daily_workload: dict[date, float],
        start_date: date,
        end_date: date,
        total_estimated_duration: float = 0.0,
        comfortable_hours: float = WORKLOAD_COMFORTABLE_HOURS,
        moderate_hours: float = WORKLOAD_MODERATE_HOURS,
    ) -> list[Text]:
        """Build all cells for the workload summary row.

        Args:
            daily_workload: Pre-computed daily workload totals
            start_date: Start date of the chart
            end_date: End date of the chart
            total_estimated_duration: Sum of all estimated durations
            comfortable_hours: Workload threshold for green zone
            moderate_hours: Workload threshold for yellow zone

        Returns:
            List of Text cells for the workload row
        """
        workload_cells = GanttCellFormatter.build_workload_cells(
            daily_workload,
            start_date,
            end_date,
            comfortable_hours=comfortable_hours,
            moderate_hours=moderate_hours,
        )

        total_est_str = (
            f"{total_estimated_duration:.1f}" if total_estimated_duration > 0 else "-"
        )

        return [
            Text("", justify="center"),
            Text(f" {GANTT_WORKLOAD_LABEL} ", style="bold yellow", justify="center"),
            Text(f" {total_est_str} ", style="bold yellow", justify="center"),
            *workload_cells,
        ]

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
