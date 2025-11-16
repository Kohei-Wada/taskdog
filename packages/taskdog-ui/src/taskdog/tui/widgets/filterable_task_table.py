"""Filterable task table widget combining search and table."""

from textual.app import ComposeResult
from textual.containers import Vertical

from taskdog.tui.events import SearchQueryChanged
from taskdog.tui.widgets.search_input import SearchInput
from taskdog.tui.widgets.task_table import TaskTable
from taskdog.view_models.task_view_model import TaskRowViewModel


class FilterableTaskTable(Vertical):
    """A task table with integrated search functionality."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the filterable task table."""
        super().__init__(*args, **kwargs)
        self.search_input: SearchInput | None = None
        self.task_table: TaskTable | None = None

    def compose(self) -> ComposeResult:
        """Compose the widget layout.

        Returns:
            Iterable of widgets to display
        """
        # Task table first (for natural focus order)
        self.task_table = TaskTable(id="task-table")
        yield self.task_table

        # Search input below the table
        self.search_input = SearchInput()
        yield self.search_input

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        if self.task_table:
            self.task_table.setup_columns()
            # Set initial focus to the task table instead of search input
            self.task_table.focus()

    def on_search_query_changed(self, event: SearchQueryChanged) -> None:
        """Handle search query changes via event.

        Args:
            event: SearchQueryChanged event with the new query string
        """
        # Filter tasks based on search query
        if self.task_table:
            self.task_table.filter_tasks(event.query)
            self._update_search_result()

    def on_search_input_submitted(self, event: SearchInput.Submitted) -> None:
        """Handle Enter key press in search input.

        Args:
            event: SearchInput submitted event
        """
        # Move focus to the task table
        if self.task_table:
            self.task_table.focus()

    @property
    def _table(self) -> TaskTable:
        """Access task table, ensuring it exists.

        Returns:
            The TaskTable instance

        Raises:
            RuntimeError: If task_table is not yet initialized
        """
        if self.task_table is None:
            raise RuntimeError("TaskTable not yet initialized")
        return self.task_table

    # Delegate methods to task_table

    def load_tasks(self, view_models: list[TaskRowViewModel]) -> None:
        """Load task ViewModels into the table."""
        self._table.load_tasks(view_models)
        self._update_search_result()

    def refresh_tasks(
        self, view_models: list[TaskRowViewModel], keep_scroll_position: bool = False
    ) -> None:
        """Refresh the table with updated ViewModels."""
        self._table.refresh_tasks(
            view_models, keep_scroll_position=keep_scroll_position
        )
        self._update_search_result()

    def get_selected_task_id(self) -> int | None:
        """Get the ID of the currently selected task."""
        return self._table.get_selected_task_id()

    def get_selected_task_vm(self) -> TaskRowViewModel | None:
        """Get the currently selected task as a ViewModel."""
        return self._table.get_selected_task_vm()

    def get_selected_task_ids(self) -> list[int]:
        """Get all selected task IDs for batch operations."""
        return self._table.get_selected_task_ids()

    def clear_selection(self) -> None:
        """Clear all task selections."""
        self._table.clear_selection()

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
    def all_viewmodels(self) -> list[TaskRowViewModel]:
        """Get all loaded ViewModels from the table."""
        return self._table.all_viewmodels
