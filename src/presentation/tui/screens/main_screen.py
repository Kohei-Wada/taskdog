"""Main screen for the TUI."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input

from infrastructure.persistence.notes_repository import NotesRepository
from presentation.tui.widgets.gantt_widget import GanttWidget
from presentation.tui.widgets.search_input import SearchInput
from presentation.tui.widgets.task_table import TaskTable


class MainScreen(Screen):
    """Main screen showing gantt chart and task list."""

    def __init__(self, notes_repository: NotesRepository, *args, **kwargs):
        """Initialize the main screen.

        Args:
            notes_repository: Notes repository for task notes operations
        """
        super().__init__(*args, **kwargs)
        self.notes_repository = notes_repository
        self.task_table: TaskTable | None = None
        self.gantt_widget: GanttWidget | None = None
        self.search_input: SearchInput | None = None

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

            # Search input (always visible between gantt and table)
            self.search_input = SearchInput()
            yield self.search_input

            # Task table section
            self.task_table = TaskTable(self.notes_repository, id="task-table")
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

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes.

        Args:
            event: Input changed event
        """
        # Only handle events from the search input
        if event.input.id != "search-input":
            return

        # Filter tasks based on search query
        if self.task_table:
            self.task_table.filter_tasks(event.value)

    def on_search_input_submitted(self, event: SearchInput.Submitted) -> None:
        """Handle Enter key press in search input.

        Args:
            event: SearchInput submitted event
        """
        # Move focus to the task table
        if self.task_table:
            self.task_table.focus()

    def show_search(self) -> None:
        """Focus the search input."""
        if self.search_input:
            self.search_input.focus_input()

    def hide_search(self) -> None:
        """Clear the search filter and return focus to table."""
        if self.search_input:
            self.search_input.clear()

        if self.task_table:
            self.task_table.clear_filter()
            self.task_table.focus()
