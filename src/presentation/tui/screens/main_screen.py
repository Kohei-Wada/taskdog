"""Main screen for the TUI."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from infrastructure.persistence.notes_repository import NotesRepository
from presentation.tui.widgets.filterable_task_table import FilterableTaskTable
from presentation.tui.widgets.gantt_widget import GanttWidget


class MainScreen(Screen[None]):
    """Main screen showing gantt chart and task list."""

    def __init__(self, notes_repository: NotesRepository, *args: Any, **kwargs: Any):
        """Initialize the main screen.

        Args:
            notes_repository: Notes repository for task notes operations
        """
        super().__init__(*args, **kwargs)
        self.notes_repository = notes_repository
        self.task_table: FilterableTaskTable | None = None
        self.gantt_widget: GanttWidget | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        yield Header(show_clock=True)

        with Vertical():
            # Gantt chart section (main display)
            self.gantt_widget = GanttWidget(id="gantt-widget")
            yield self.gantt_widget

            # Filterable task table (search + table)
            self.task_table = FilterableTaskTable(self.notes_repository, id="filterable-task-table")
            yield self.task_table

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize gantt with empty message
        if self.gantt_widget:
            self.gantt_widget.update("Loading gantt chart...")

        # Focus on the task table
        if self.task_table:
            self.task_table.focus_table()

    def show_search(self) -> None:
        """Focus the search input."""
        if self.task_table:
            self.task_table.show_search()

    def hide_search(self) -> None:
        """Clear the search filter and return focus to table."""
        if self.task_table:
            self.task_table.hide_search()
