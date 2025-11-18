"""Main screen for the TUI."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Header

from taskdog.tui.events import SearchQueryChanged
from taskdog.tui.state import TUIState
from taskdog.tui.widgets.custom_footer import CustomFooter
from taskdog.tui.widgets.gantt_widget import GanttWidget
from taskdog.tui.widgets.search_input import SearchInput
from taskdog.tui.widgets.task_table import TaskTable
from taskdog.view_models.task_view_model import TaskRowViewModel


class MainScreen(Screen[None]):
    """Main screen showing gantt chart and task list."""

    BINDINGS: ClassVar = [
        Binding("ctrl+j", "focus_next", "Next widget", show=False, priority=True),
        Binding(
            "ctrl+k", "focus_previous", "Previous widget", show=False, priority=True
        ),
    ]

    def __init__(self, state: TUIState | None = None) -> None:
        """Initialize the main screen.

        Args:
            state: TUI state for connection status (optional for backward compatibility)
        """
        super().__init__()
        self.state = state
        self.task_table: TaskTable | None = None
        self.gantt_widget: GanttWidget | None = None
        self.search_input: SearchInput | None = None
        self.custom_footer: CustomFooter | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        # Header (simplified, no connection status)
        yield Header(show_clock=True, id="main-header")

        with Vertical():
            # Gantt chart section (main display)
            self.gantt_widget = GanttWidget(id="gantt-widget")
            self.gantt_widget.border_title = "Gantt Chart"
            yield self.gantt_widget

            # Task table (main content)
            self.task_table = TaskTable(id="task-table")  # type: ignore[no-untyped-call]
            self.task_table.border_title = "Tasks"
            yield self.task_table

            # Search input at the bottom (Vim-style)
            self.search_input = SearchInput(id="main-search-input")
            yield self.search_input

        # Custom footer with keybindings and connection status
        if self.state:
            self.custom_footer = CustomFooter(self.state, id="custom-footer")
            yield self.custom_footer

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize gantt with empty message
        if self.gantt_widget:
            self.gantt_widget.update("Loading gantt chart...")

        # Setup task table columns
        if self.task_table:
            self.task_table.setup_columns()  # type: ignore[no-untyped-call]
            self.task_table.focus()

    def on_search_query_changed(self, event: SearchQueryChanged) -> None:
        """Handle search query changes.

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
        # Move focus back to the task table
        if self.task_table:
            self.task_table.focus()

    def on_search_input_refine_filter(self, event: SearchInput.RefineFilter) -> None:
        """Handle Ctrl+R key press in search input to refine filter.

        Args:
            event: SearchInput RefineFilter event
        """
        self._refine_filter()

    def _refine_filter(self) -> None:
        """Add current search query to filter chain for progressive filtering."""
        if not self.search_input or not self.task_table:
            return

        current_query = self.search_input.value
        if not current_query:
            return

        # Add current query to filter chain
        self.task_table.add_filter_to_chain(current_query)

        # Clear search input for new query
        self.search_input.clear_input_only()

        # Update filter chain display
        filter_chain = self.task_table.filter_chain
        self.search_input.update_filter_chain(filter_chain)

        # Reapply filters to show refined results
        self.task_table.filter_tasks("")

        # Update search result count
        self._update_search_result()

    def show_search(self) -> None:
        """Focus the search input."""
        if self.search_input:
            self.search_input.focus_input()

    def hide_search(self) -> None:
        """Clear the search filter and return focus to table."""
        if self.search_input:
            self.search_input.clear()

        if self.task_table:
            self.task_table.clear_filter()  # type: ignore[no-untyped-call]
            self.task_table.focus()

    def _update_search_result(self) -> None:
        """Update the search result count display."""
        if self.search_input and self.task_table:
            matched = self.task_table.match_count
            total = self.task_table.total_count
            self.search_input.update_result(matched, total)

    # Delegate methods to task_table for compatibility

    def load_tasks(self, view_models: list[TaskRowViewModel]) -> None:
        """Load task ViewModels into the table."""
        if self.task_table:
            self.task_table.load_tasks(view_models)
            self._update_search_result()

    def refresh_tasks(
        self, view_models: list[TaskRowViewModel], keep_scroll_position: bool = False
    ) -> None:
        """Refresh the table with updated ViewModels."""
        if self.task_table:
            self.task_table.refresh_tasks(
                view_models, keep_scroll_position=keep_scroll_position
            )
            self._update_search_result()

    def get_selected_task_id(self) -> int | None:
        """Get the ID of the currently selected task."""
        if self.task_table:
            return self.task_table.get_selected_task_id()
        return None

    def get_selected_task_vm(self) -> TaskRowViewModel | None:
        """Get the currently selected task as a ViewModel."""
        if self.task_table:
            return self.task_table.get_selected_task_vm()
        return None

    def get_selected_task_ids(self) -> list[int]:
        """Get all selected task IDs for batch operations."""
        if self.task_table:
            return self.task_table.get_selected_task_ids()
        return []

    def clear_selection(self) -> None:
        """Clear all task selections."""
        if self.task_table:
            self.task_table.clear_selection()

    def focus_table(self) -> None:
        """Focus the task table."""
        if self.task_table:
            self.task_table.focus()

    @property
    def all_viewmodels(self) -> list[TaskRowViewModel]:
        """Get all loaded ViewModels from the table."""
        if self.task_table:
            return self.task_table.all_viewmodels
        return []

    def action_focus_next(self) -> None:
        """Move focus to the next widget (Ctrl+J)."""
        self.screen.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to the previous widget (Ctrl+K)."""
        self.screen.focus_previous()
