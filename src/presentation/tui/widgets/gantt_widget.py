"""Gantt chart widget for TUI.

This widget wraps the GanttDataTable and provides additional functionality
like date range management and automatic resizing.
"""

from datetime import date, timedelta

from textual.app import ComposeResult
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

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        self._gantt_table = GanttDataTable()
        yield self._gantt_table

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
            # Show empty message using a single-row table
            self._gantt_table.clear(columns=True)
            self._gantt_table.add_column("Message")
            self._gantt_table.add_row("[dim]No tasks to display[/dim]")
            return

        # Get widget width for proper rendering
        widget_width = self.size.width if self.size else DEFAULT_GANTT_WIDGET_WIDTH
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)

        # Calculate optimal date range based on available width
        timeline_width = max(console_width - GANTT_TABLE_FIXED_WIDTH, MIN_TIMELINE_WIDTH)
        max_days = timeline_width // CHARS_PER_DAY

        # Round to nearest week for cleaner display
        weeks = max(max_days // DAYS_PER_WEEK, 1)
        display_days = weeks * DAYS_PER_WEEK

        # Calculate date range
        start_date = self._start_date
        end_date = self._end_date

        if not start_date and not end_date:
            # Auto-calculate range: show today + rounded weeks
            today = date.today()
            start_date = today
            end_date = today + timedelta(days=display_days - 1)
        elif start_date and end_date:
            # Both dates provided - check if they fit in screen width
            date_range_days = (end_date - start_date).days + 1
            if date_range_days > display_days:
                # Range too large, clip to display_days centered around today
                today = date.today()
                half_days = display_days // DISPLAY_HALF_WIDTH_DIVISOR
                start_date = today - timedelta(days=half_days)
                end_date = start_date + timedelta(days=display_days - 1)

        # Get Gantt data from Application layer
        repository = JsonTaskRepository(XDGDirectories.get_tasks_file())
        task_query_service = TaskQueryService(repository)

        # Create a filter that returns the current tasks
        class TaskListFilter(TaskFilter):
            def __init__(self, tasks):
                self.tasks = tasks

            def filter(self, tasks):
                # Return only tasks that match our task IDs
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

        # Load data into the GanttDataTable
        try:
            self._gantt_table.load_gantt(gantt_result)
        except Exception as e:
            # Show error message
            self._gantt_table.clear(columns=True)
            self._gantt_table.add_column("Error")
            self._gantt_table.add_row(f"[red]Error rendering gantt: {e!s}[/red]")

    def on_resize(self):
        """Handle resize events."""
        if self._tasks:
            self._render_gantt()
