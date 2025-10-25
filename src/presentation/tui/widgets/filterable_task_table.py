"""Filterable task table widget combining search and table."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from domain.entities.task import Task
from infrastructure.persistence.notes_repository import NotesRepository
from presentation.tui.widgets.search_input import SearchInput
from presentation.tui.widgets.task_table import TaskTable


class FilterableTaskTable(Vertical):
    """A task table with integrated search functionality."""

    def __init__(self, notes_repository: NotesRepository, *args, **kwargs):
        """Initialize the filterable task table.

        Args:
            notes_repository: Notes repository for task notes operations
        """
        super().__init__(*args, **kwargs)
        self.notes_repository = notes_repository
        self.search_input: SearchInput | None = None
        self.task_table: TaskTable | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        self.search_input = SearchInput()
        yield self.search_input

        self.task_table = TaskTable(self.notes_repository, id="task-table")
        yield self.task_table

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        if self.task_table:
            self.task_table.setup_columns()

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
            self._update_search_result()

    def on_search_input_submitted(self, event: SearchInput.Submitted) -> None:
        """Handle Enter key press in search input.

        Args:
            event: SearchInput submitted event
        """
        # Move focus to the task table
        if self.task_table:
            self.task_table.focus()

    # Delegate methods to task_table

    def load_tasks(self, tasks: list[Task]) -> None:
        """Load tasks into the table.

        Args:
            tasks: List of tasks to display
        """
        if self.task_table:
            self.task_table.load_tasks(tasks)
            self._update_search_result()

    def refresh_tasks(self, tasks: list[Task]) -> None:
        """Refresh the table with updated tasks.

        Args:
            tasks: List of tasks to display
        """
        if self.task_table:
            self.task_table.refresh_tasks(tasks)
            self._update_search_result()

    def get_selected_task(self) -> Task | None:
        """Get the currently selected task.

        Returns:
            The selected Task, or None if no task is selected
        """
        if self.task_table:
            return self.task_table.get_selected_task()
        return None

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

    def focus_table(self) -> None:
        """Focus the task table."""
        if self.task_table:
            self.task_table.focus()

    def _update_search_result(self) -> None:
        """Update the search result count display."""
        if self.search_input and self.task_table:
            matched = self.task_table.match_count
            total = self.task_table.total_count
            self.search_input.update_result(matched, total)

    @property
    def _all_tasks(self) -> list[Task]:
        """Get all tasks (for compatibility with app.py).

        Returns:
            List of all tasks
        """
        if self.task_table:
            return self.task_table._all_tasks
        return []
