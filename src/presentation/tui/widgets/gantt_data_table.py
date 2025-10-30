"""Gantt chart data table widget for TUI.

This widget provides a Textual DataTable-based Gantt chart implementation,
independent of the CLI's RichGanttRenderer. It supports interactive features
like task selection, date range adjustment, and filtering.
"""

from datetime import date, timedelta
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.widgets import DataTable

from application.dto.gantt_result import GanttResult
from domain.entities.task import Task
from presentation.constants.table_dimensions import (
    GANTT_TABLE_EST_HOURS_WIDTH,
    GANTT_TABLE_ID_WIDTH,
    GANTT_TABLE_TASK_MIN_WIDTH,
)
from presentation.renderers.gantt_cell_formatter import GanttCellFormatter

if TYPE_CHECKING:
    from shared.utils.holiday_checker import HolidayChecker

# Constants
GANTT_HEADER_ROW_COUNT = 3  # Number of header rows (Month, Week, Date)


class GanttDataTable(DataTable):
    """A Textual DataTable widget for displaying Gantt charts.

    This widget provides a read-only Gantt chart display with:
    - Dynamic date range adjustment
    - Workload visualization
    - Status-based coloring
    """

    # No bindings - read-only display
    BINDINGS: ClassVar = []

    def __init__(self, holiday_checker: "HolidayChecker | None" = None, *args, **kwargs):
        """Initialize the Gantt data table.

        Args:
            holiday_checker: Optional HolidayChecker for holiday detection
        """
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
        self._holiday_checker = holiday_checker

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

        # Add fixed columns with centered headers
        self.add_column(Text("ID", justify="center"), width=GANTT_TABLE_ID_WIDTH)
        self.add_column(Text("Task", justify="center"), width=GANTT_TABLE_TASK_MIN_WIDTH)
        self.add_column(Text("Est[h]", justify="center"), width=GANTT_TABLE_EST_HOURS_WIDTH)

        # Add single Timeline column (contains all dates)
        # Store date range for later use
        days = (end_date - start_date).days + 1
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            self._date_columns.append(current_date)

        # Single Timeline column with centered header
        self.add_column(Text("Timeline", justify="center"))

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
            self._task_map[idx + GANTT_HEADER_ROW_COUNT] = task

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
        # Get the three header lines from the formatter
        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, self._holiday_checker
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
        task_id, task_name, est_hours = self._format_task_metadata(task)
        timeline = self._build_timeline(task, task_daily_hours, start_date, end_date)

        self.add_row(
            Text(task_id, justify="center"),
            Text.from_markup(task_name, justify="left"),
            Text(est_hours, justify="center"),
            timeline,
        )

    def _format_task_metadata(self, task: Task) -> tuple[str, str, str]:
        """Format fixed column metadata for a task.

        Args:
            task: Task to format

        Returns:
            Tuple of (task_id, task_name, estimated_hours)
        """
        task_id = str(task.id)

        # Task name with strikethrough for completed and canceled tasks
        task_name = task.name
        if task.is_finished:
            task_name = f"[strike]{task_name}[/strike]"

        # Estimated hours
        est_hours = f"{task.estimated_duration:.1f}" if task.estimated_duration else "-"

        return task_id, task_name, est_hours

    def _build_timeline(
        self,
        task: Task,
        task_daily_hours: dict[date, float],
        start_date: date,
        end_date: date,
    ) -> Text:
        """Build timeline visualization for a task.

        Args:
            task: Task to build timeline for
            task_daily_hours: Daily hours allocation
            start_date: Start date of timeline
            end_date: End date of timeline

        Returns:
            Rich Text object with formatted timeline
        """
        days = (end_date - start_date).days + 1
        parsed_dates = GanttCellFormatter.parse_task_dates(task)
        timeline = Text()

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            hours = task_daily_hours.get(current_date, 0.0)

            # Get formatted cell from formatter
            display, style = GanttCellFormatter.format_timeline_cell(
                current_date,
                hours,
                parsed_dates,
                task.status,
                self._holiday_checker,
            )
            timeline.append(display, style=style)

        return timeline

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
        # Build workload timeline using the formatter
        workload_timeline = GanttCellFormatter.build_workload_timeline(
            daily_workload, start_date, end_date
        )

        self.add_row(
            Text("", justify="center"),
            Text("Workload[h]", style="bold yellow", justify="center"),
            Text("", justify="center"),
            workload_timeline,
        )

    def get_legend_text(self) -> Text:
        """Build legend text for the Gantt chart.

        Returns:
            Rich Text object with legend
        """
        return GanttCellFormatter.build_legend()
