"""Gantt chart widget for TUI."""

from datetime import date

from rich.console import Console
from textual.widgets import Static

from domain.entities.task import Task
from presentation.constants.table_dimensions import (
    BORDER_WIDTH,
    CHARS_PER_DAY,
    DEFAULT_GANTT_WIDGET_WIDTH,
    DISPLAY_HALF_WIDTH_DIVISOR,
    GANTT_TABLE_FIXED_WIDTH,
    MIN_CONSOLE_WIDTH,
    MIN_TIMELINE_WIDTH,
)
from shared.constants.time import DAYS_PER_WEEK


class GanttWidget(Static):
    """A widget for displaying gantt chart."""

    def __init__(self, *args, **kwargs):
        """Initialize the gantt widget."""
        super().__init__(*args, **kwargs)
        self._tasks: list[Task] = []
        self._start_date: date | None = None
        self._end_date: date | None = None

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
        if not self._tasks:
            self.update("No tasks to display")
            return

        # Import here to avoid circular imports
        from datetime import timedelta

        from application.queries.task_query_service import TaskQueryService
        from infrastructure.persistence.json_task_repository import JsonTaskRepository
        from presentation.console.rich_console_writer import RichConsoleWriter
        from presentation.renderers.rich_gantt_renderer import RichGanttRenderer

        # Get widget width for proper rendering
        # Use content region width to account for borders and padding
        widget_width = self.size.width if self.size else DEFAULT_GANTT_WIDGET_WIDTH
        # Subtract border width (for left and right borders)
        console_width = max(widget_width - BORDER_WIDTH, MIN_CONSOLE_WIDTH)

        # Calculate optimal date range based on available width
        # Timeline column gets the rest
        timeline_width = max(
            console_width - GANTT_TABLE_FIXED_WIDTH, MIN_TIMELINE_WIDTH
        )  # Minimum timeline width
        # Each day takes CHARS_PER_DAY characters (e.g., "16 ")
        max_days = timeline_width // CHARS_PER_DAY

        # Round to nearest week for cleaner display
        # e.g., 25 days → 21 days (3 weeks), 18 days → 14 days (2 weeks)
        weeks = max(max_days // DAYS_PER_WEEK, 1)  # At least 1 week
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
        # Note: TUI already has filtered tasks, but we need to use TaskQueryService
        # to get the full GanttResult with workload calculations
        from shared.xdg_utils import XDGDirectories

        repository = JsonTaskRepository(XDGDirectories.get_tasks_file())
        task_query_service = TaskQueryService(repository)

        # Create a simple filter that returns the current tasks
        # This is a workaround since we already have the filtered tasks
        from application.queries.filters.task_filter import TaskFilter

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

        # Create console with widget width
        console = Console(width=console_width, force_terminal=True)
        console_writer = RichConsoleWriter(console)
        renderer = RichGanttRenderer(console_writer)

        # Build the table with legend as caption
        # Textual's Static widget can render Rich Table objects directly
        try:
            table = renderer.build_table(gantt_result)
            if table:
                # Table already includes legend as caption
                self.update(table)
            else:
                self.update("No tasks to display")
        except Exception as e:
            self.update(f"Error rendering gantt: {e!s}")

    def on_resize(self):
        """Handle resize events."""
        if self._tasks:
            self._render_gantt()
