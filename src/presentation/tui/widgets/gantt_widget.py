"""Gantt chart widget for TUI."""

from datetime import date

from rich.console import Console
from textual.widgets import Static

from domain.entities.task import Task


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

        from presentation.console.rich_console_writer import RichConsoleWriter
        from presentation.renderers.rich_gantt_renderer import RichGanttRenderer

        # Get widget width for proper rendering
        # Use content region width to account for borders and padding
        widget_width = self.size.width if self.size else 120
        # Subtract border width (2 for left and right borders)
        console_width = max(widget_width - 2, 80)

        # Calculate optimal date range based on available width
        # Table columns: ID(4) + Task(20) + Est(7) + borders/padding(~16) = ~47 chars
        # Timeline column gets the rest
        timeline_width = max(console_width - 47, 30)  # Minimum 30 chars for timeline
        # Each day takes 3 characters (e.g., "16 ")
        max_days = timeline_width // 3

        # Round to nearest week (7 days) for cleaner display
        # e.g., 25 days → 21 days (3 weeks), 18 days → 14 days (2 weeks)
        weeks = max(max_days // 7, 1)  # At least 1 week
        display_days = weeks * 7

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
                half_days = display_days // 2
                start_date = today - timedelta(days=half_days)
                end_date = start_date + timedelta(days=display_days - 1)

        # Create console with widget width
        console = Console(width=console_width, force_terminal=True)
        console_writer = RichConsoleWriter(console)
        renderer = RichGanttRenderer(console_writer)

        # Build the table and update widget directly
        # Textual's Static widget can render Rich Table objects directly
        try:
            table = renderer.build_table(self._tasks, start_date, end_date)
            if table:
                self.update(table)
            else:
                self.update("No tasks to display")
        except Exception as e:
            self.update(f"Error rendering gantt: {e!s}")

    def on_resize(self):
        """Handle resize events."""
        if self._tasks:
            self._render_gantt()
