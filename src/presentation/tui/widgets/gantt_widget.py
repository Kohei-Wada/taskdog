"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from datetime import date, timedelta

from textual.app import ComposeResult
from textual.containers import Center
from textual.widgets import Static

from application.queries.filters.task_filter import TaskFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.constants.table_dimensions import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    DISPLAY_HALF_WIDTH_DIVISOR,
    GANTT_TABLE_FIXED_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_TIMELINE_WIDTH,
)
from presentation.tui.widgets.gantt_data_table import GanttDataTable
from shared.constants.time import DAYS_PER_WEEK
from shared.utils.date_utils import get_previous_monday
from shared.xdg_utils import XDGDirectories


class GanttWidget(Static):
    """A widget for displaying gantt chart using GanttDataTable.

    This widget manages the GanttDataTable and handles date range calculations
    based on available screen width.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self._tasks: list[Task] = []
        self._start_date: date | None = None
        self._end_date: date | None = None
        self._gantt_table: GanttDataTable | None = None
        self._title_widget: Static | None = None
        self._legend_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        # Title above the table
        self._title_widget = Static("")
        self._title_widget.styles.text_align = "center"
        self._title_widget.styles.margin = (0, 0, 1, 0)  # Bottom margin
        yield self._title_widget

        self._gantt_table = GanttDataTable()
        self._gantt_table.styles.border = ("solid", "white")
        self._gantt_table.styles.width = "auto"

        # Wrap table in Center container for horizontal centering
        with Center():
            yield self._gantt_table

        # Legend below the table
        self._legend_widget = Static("")
        self._legend_widget.styles.text_align = "center"
        self._legend_widget.styles.margin = (1, 0, 0, 0)  # Top margin
        yield self._legend_widget

    def update_gantt(
        self,
        tasks: list[Task],
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        """Update the gantt chart with new tasks.

        Args:
            tasks: List of tasks to display
            start_date: Optional start date for the chart
            end_date: Optional end date for the chart
        """
        self._tasks = tasks
        self._start_date = start_date
        self._end_date = end_date
        self._render_gantt()

    def _render_gantt(self):
        """Render the gantt chart."""
        if not self._gantt_table:
            return

        if not self._tasks:
            self._show_empty_message()
            return

        display_days = self._calculate_display_days()
        start_date, end_date = self._calculate_date_range(display_days)
        self._load_gantt_data(start_date, end_date)

    def _show_empty_message(self):
        """Show empty message when no tasks are available."""
        self._gantt_table.clear(columns=True)
        self._gantt_table.add_column("Message")
        self._gantt_table.add_row("[dim]No tasks to display[/dim]")

    def _calculate_display_days(self) -> int:
        """Calculate optimal number of days to display.

        Returns:
            Number of days to display (rounded to weeks)
        """
        widget_width = self.size.width if self.size else DEFAULT_GANTT_WIDGET_WIDTH
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)
        timeline_width = max(console_width - GANTT_TABLE_FIXED_WIDTH, MIN_TIMELINE_WIDTH)
        max_days = timeline_width // CHARS_PER_DAY
        weeks = max(max_days // DAYS_PER_WEEK, 1)
        return weeks * DAYS_PER_WEEK

    def _calculate_date_range(self, display_days: int) -> tuple[date, date]:
        """Calculate start and end dates for the chart.

        Args:
            display_days: Number of days to display

        Returns:
            Tuple of (start_date, end_date)
        """
        start_date = self._start_date
        end_date = self._end_date

        if not start_date and not end_date:
            start_date = get_previous_monday()
            end_date = start_date + timedelta(days=display_days - 1)
        elif start_date and end_date:
            date_range_days = (end_date - start_date).days + 1
            if date_range_days > display_days:
                today = date.today()
                half_days = display_days // DISPLAY_HALF_WIDTH_DIVISOR
                start_date = today - timedelta(days=half_days)
                end_date = start_date + timedelta(days=display_days - 1)

        return start_date, end_date

    def _load_gantt_data(self, start_date: date, end_date: date):
        """Load and display gantt data.

        Args:
            start_date: Start date for the chart
            end_date: End date for the chart
        """
        repository = JsonTaskRepository(XDGDirectories.get_tasks_file())
        task_query_service = TaskQueryService(repository)

        class TaskListFilter(TaskFilter):
            def __init__(self, tasks):
                self.tasks = tasks

            def filter(self, tasks):
                task_ids = {t.id for t in self.tasks}
                return [t for t in tasks if t.id in task_ids]

        filter_obj = TaskListFilter(self._tasks)
        gantt_result = task_query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by="planned_start",
            reverse=False,
            start_date=start_date,
            end_date=end_date,
        )

        try:
            self._gantt_table.load_gantt(gantt_result)

            # Update title with date range
            if self._title_widget:
                title_text = f"[bold yellow]Gantt Chart[/bold yellow] [dim]({start_date} to {end_date})[/dim]"
                self._title_widget.update(title_text)

            # Update legend
            if self._legend_widget:
                legend_text = self._gantt_table.get_legend_text()
                self._legend_widget.update(legend_text)
        except Exception as e:
            self._show_error_message(e)

    def _show_error_message(self, error: Exception):
        """Show error message when rendering fails.

        Args:
            error: The exception that occurred
        """
        self._gantt_table.clear(columns=True)
        self._gantt_table.add_column("Error")
        self._gantt_table.add_row(f"[red]Error rendering gantt: {error!s}[/red]")
        if self._title_widget:
            self._title_widget.update("")
        if self._legend_widget:
            self._legend_widget.update("")

    def on_resize(self):
        """Handle resize events."""
        if self._tasks:
            # Schedule re-render after the resize completes
            self.call_after_refresh(self._render_gantt)
