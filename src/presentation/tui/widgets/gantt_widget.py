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
        from presentation.console.rich_console_writer import RichConsoleWriter
        from presentation.renderers.rich_gantt_renderer import RichGanttRenderer

        # Create a minimal console for the renderer (width doesn't matter for TUI)
        console = Console()
        console_writer = RichConsoleWriter(console)
        renderer = RichGanttRenderer(console_writer)

        # Build the table and update widget directly
        # Textual's Static widget can render Rich Table objects directly
        try:
            table = renderer.build_table(self._tasks, self._start_date, self._end_date)
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
