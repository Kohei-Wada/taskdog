"""Main screen for the TUI."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header

from presentation.tui.widgets.gantt_widget import GanttWidget
from presentation.tui.widgets.task_table import TaskTable


class MainScreen(Screen):
    """Main screen showing gantt chart and task list."""

    def __init__(self, *args, **kwargs):
        """Initialize the main screen."""
        super().__init__(*args, **kwargs)
        self.task_table: TaskTable | None = None
        self.gantt_widget: GanttWidget | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        yield Header(show_clock=True)

        with VerticalScroll():
            # Gantt chart section (main display)
            self.gantt_widget = GanttWidget(id="gantt-widget")
            yield self.gantt_widget

            # Task table section
            self.task_table = TaskTable(id="task-table")
            self.task_table.setup_columns()
            yield self.task_table

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize gantt with empty message
        if self.gantt_widget:
            self.gantt_widget.update("Loading gantt chart...")

        # Focus on the table
        if self.task_table:
            self.task_table.focus()
