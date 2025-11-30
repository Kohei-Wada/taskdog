"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import ClassVar

from rich.text import Text
from textual.widgets import DataTable

from taskdog.constants.table_dimensions import (
    GANTT_TABLE_EST_HOURS_WIDTH,
    GANTT_TABLE_ID_WIDTH,
    GANTT_TABLE_TASK_MIN_WIDTH,
)
from taskdog.renderers.gantt_cell_formatter import GanttCellFormatter
from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel

# Constants
GANTT_HEADER_ROW_COUNT = 3  # Number of header rows (Month, Week, Date)


class GanttDataTable(DataTable):
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides a read-only Gantt chart display with:
    - Dynamic date range adjustment
    - Workload visualization
    - Status-based coloring
    - Differential rendering for performance
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
        self._task_map: dict[
            int, TaskGanttRowViewModel
        ] = {}  # Maps row index to TaskViewModel
        # NOTE: _gantt_view_model removed - data passed as parameter to load_gantt (Step 4)
        self._date_columns: list[date] = []  # Columns representing dates

        # State for differential rendering
        self._cached_date_range: tuple[date, date] | None = None
        self._workload_row_exists: bool = False

    def setup_columns(
        self,
        start_date: date,
        end_date: date,
    ) -> bool:
        """Set up table columns including Timeline column.

        Only rebuilds columns if the date range has changed.

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart

        Returns:
            True if columns were rebuilt, False if reused
        """
        new_range = (start_date, end_date)
        if self._cached_date_range == new_range:
            return False  # Reuse existing columns

        self._cached_date_range = new_range

        # Clear existing columns
        self.clear(columns=True)
        self._date_columns.clear()
        self._task_map.clear()
        self._workload_row_exists = False

        # Add fixed columns with centered headers
        self.add_column(Text("ID", justify="center"), width=GANTT_TABLE_ID_WIDTH)
        self.add_column(
            Text("Task", justify="center"), width=GANTT_TABLE_TASK_MIN_WIDTH
        )
        self.add_column(
            Text("Est[h]", justify="center"), width=GANTT_TABLE_EST_HOURS_WIDTH
        )

        # Add single Timeline column (contains all dates)
        # Store date range for later use
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)

        # Single Timeline column with centered header
        self.add_column(Text("Timeline", justify="center"))

        return True

    def load_gantt(self, gantt_view_model: GanttViewModel):
        """Load Gantt data into the table.

        Uses differential rendering when the date range is unchanged,
        falling back to full rebuild when columns need to change.

        Args:
            gantt_view_model: Presentation-ready Gantt data
        """
        # Setup columns based on date range (returns True if rebuilt)
        columns_rebuilt = self.setup_columns(
            gantt_view_model.start_date,
            gantt_view_model.end_date,
        )

        if gantt_view_model.is_empty():
            # Clear any existing rows if columns were not rebuilt
            if not columns_rebuilt:
                self._clear_all_rows()
            return

        if columns_rebuilt:
            # Full rebuild needed after column change
            self._full_rebuild(gantt_view_model)
        else:
            # Differential update - only update changed cells
            self._differential_update(gantt_view_model)

    def _clear_all_rows(self):
        """Clear all rows while preserving column structure."""
        while self.row_count > 0:
            row_key, _ = self.coordinate_to_cell_key((self.row_count - 1, 0))
            self.remove_row(row_key)
        self._task_map.clear()
        self._workload_row_exists = False

    def _full_rebuild(self, gantt_view_model: GanttViewModel):
        """Perform full table rebuild (after column structure change).

        Args:
            gantt_view_model: Presentation-ready Gantt data
        """
        # Add date header rows (Month, Today marker, Day)
        self._add_date_header_rows(
            gantt_view_model.start_date,
            gantt_view_model.end_date,
            gantt_view_model.holidays,
        )

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
        self._workload_row_exists = True

    def _differential_update(self, gantt_view_model: GanttViewModel):
        """Update table using differential rendering.

        Updates existing rows using update_cell_at() instead of clearing
        and rebuilding. Only adds/removes rows when the count changes.

        Args:
            gantt_view_model: Presentation-ready Gantt data
        """
        # Calculate current task row count (excluding headers and workload row)
        current_task_row_count = self._get_task_row_count()
        new_task_count = len(gantt_view_model.tasks)

        # Update header rows (they may have changed due to "today" marker)
        self._update_date_header_rows(
            gantt_view_model.start_date,
            gantt_view_model.end_date,
            gantt_view_model.holidays,
        )

        # Update existing task rows or add new ones
        for idx, task_vm in enumerate(gantt_view_model.tasks):
            task_daily_hours = gantt_view_model.task_daily_hours.get(task_vm.id, {})
            row_idx = GANTT_HEADER_ROW_COUNT + idx

            if idx < current_task_row_count:
                # Update existing row
                self._update_task_row(
                    row_idx,
                    task_vm,
                    task_daily_hours,
                    gantt_view_model.start_date,
                    gantt_view_model.end_date,
                    gantt_view_model.holidays,
                )
            else:
                # Add new row
                self._add_task_row(
                    task_vm,
                    task_daily_hours,
                    gantt_view_model.start_date,
                    gantt_view_model.end_date,
                    gantt_view_model.holidays,
                )
            self._task_map[row_idx] = task_vm

        # Remove excess task rows (from end, before workload row)
        self._remove_excess_task_rows(new_task_count)

        # Update or add workload row
        self._update_or_add_workload_row(
            gantt_view_model.daily_workload,
            gantt_view_model.start_date,
            gantt_view_model.end_date,
            gantt_view_model.total_estimated_duration,
        )

    def _get_task_row_count(self) -> int:
        """Get the number of task rows (excluding headers and workload)."""
        total_rows = self.row_count
        if total_rows <= GANTT_HEADER_ROW_COUNT:
            return 0
        # Subtract header rows and workload row (if exists)
        return (
            total_rows
            - GANTT_HEADER_ROW_COUNT
            - (1 if self._workload_row_exists else 0)
        )

    def _remove_excess_task_rows(self, new_count: int):
        """Remove task rows beyond new_count, preserving workload row.

        Args:
            new_count: The desired number of task rows
        """
        while self._get_task_row_count() > new_count:
            # Calculate the index of the last task row
            task_row_idx = GANTT_HEADER_ROW_COUNT + self._get_task_row_count() - 1

            # Remove from _task_map first
            if task_row_idx in self._task_map:
                del self._task_map[task_row_idx]

            # Get the row key and remove it
            row_key, _ = self.coordinate_to_cell_key((task_row_idx, 0))
            self.remove_row(row_key)

    def _add_date_header_rows(
        self, start_date: date, end_date: date, holidays: set[date]
    ):
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

    def _update_date_header_rows(
        self, start_date: date, end_date: date, holidays: set[date]
    ):
        """Update existing date header rows using update_cell_at().

        Args:
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        # Get the three header lines from the formatter
        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, holidays
        )

        # Update the three header rows (indices 0, 1, 2)
        # Row 0: Month header
        self.update_cell_at((0, 3), month_line)
        # Row 1: Today marker
        self.update_cell_at((1, 3), today_line)
        # Row 2: Day header
        self.update_cell_at((2, 3), day_line)

    def _add_task_row(
        self,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ):
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

    def _update_task_row(
        self,
        row_idx: int,
        task_vm: TaskGanttRowViewModel,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
        holidays: set[date],
    ):
        """Update an existing task row using update_cell_at().

        Args:
            row_idx: Row index to update
            task_vm: Task ViewModel to update with
            task_daily_hours: Daily hours allocation for this task
            start_date: Start date of the chart
            end_date: End date of the chart
            holidays: Set of holiday dates for styling
        """
        task_id, task_name, est_hours = self._format_task_metadata(task_vm)
        timeline = self._build_timeline(
            task_vm, task_daily_hours, start_date, end_date, holidays
        )

        # Update each cell individually using update_cell_at()
        self.update_cell_at((row_idx, 0), Text(task_id, justify="center"))
        self.update_cell_at((row_idx, 1), Text.from_markup(task_name, justify="left"))
        self.update_cell_at((row_idx, 2), Text(est_hours, justify="center"))
        self.update_cell_at((row_idx, 3), timeline)

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
    ):
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

    def _update_or_add_workload_row(
        self,
        daily_workload: dict[date, float],
        start_date: date,
        end_date: date,
        total_estimated_duration: float = 0.0,
    ):
        """Update existing workload row or add new one.

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

        if self._workload_row_exists:
            # Update existing workload row (last row)
            workload_row_idx = self.row_count - 1
            self.update_cell_at((workload_row_idx, 0), Text("", justify="center"))
            self.update_cell_at(
                (workload_row_idx, 1),
                Text("Est. Workload[h]", style="bold yellow", justify="center"),
            )
            self.update_cell_at(
                (workload_row_idx, 2),
                Text(total_est_str, style="bold yellow", justify="center"),
            )
            self.update_cell_at((workload_row_idx, 3), workload_timeline)
        else:
            # Add new workload row
            self.add_row(
                Text("", justify="center"),
                Text("Est. Workload[h]", style="bold yellow", justify="center"),
                Text(total_est_str, style="bold yellow", justify="center"),
                workload_timeline,
            )
            self._workload_row_exists = True

    def get_legend_text(self) -> Text:
        """Build legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        return GanttCellFormatter.build_legend()
