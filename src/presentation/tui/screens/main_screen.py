"""Main screen for the TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from presentation.tui.widgets.dashboard_widget import DashboardWidget
from presentation.tui.widgets.gantt_widget import GanttWidget
from presentation.tui.widgets.task_table import TaskTable


class MainScreen(Screen):
    """Main screen showing gantt chart and task list."""

    def __init__(self, *args, **kwargs):
        """Initialize the main screen."""
        super().__init__(*args, **kwargs)
        self.dashboard_widget: DashboardWidget | None = None
        self.task_table: TaskTable | None = None
        self.gantt_widget: GanttWidget | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        yield Header(show_clock=True)

        with VerticalScroll():
            yield Static(
                "[bold cyan]Taskdog TUI[/bold cyan] - Task Management Interface",
                id="title",
            )

            # Gantt chart section (main display)
            yield Static("[bold yellow]Gantt Chart[/bold yellow]", id="gantt-title")
            self.gantt_widget = GanttWidget(id="gantt-widget")
            yield self.gantt_widget

            # Horizontal layout for table and dashboard
            with Horizontal(id="bottom-section"):
                # Left side: Task table
                with Container(id="table-container"):
                    yield Static("[bold yellow]Task List[/bold yellow]", id="table-title")
                    self.task_table = TaskTable(id="task-table")
                    self.task_table.setup_columns()
                    yield self.task_table

                # Right side: Dashboard
                with Container(id="dashboard-container"):
                    yield Static("[bold yellow]Dashboard[/bold yellow]", id="dashboard-title")
                    self.dashboard_widget = DashboardWidget(id="dashboard-widget")
                    yield self.dashboard_widget

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize dashboard with empty message
        if self.dashboard_widget:
            self.dashboard_widget.update("Loading dashboard...")

        # Initialize gantt with empty message
        if self.gantt_widget:
            self.gantt_widget.update("Loading gantt chart...")

        # Focus on the table
        if self.task_table:
            self.task_table.focus()
