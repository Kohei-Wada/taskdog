"""Main screen for the TUI."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Header

from taskdog.tui.events import FilterChanged, SearchQueryChanged
from taskdog.tui.state import TUIState
from taskdog.tui.widgets.custom_footer import CustomFooter
from taskdog.tui.widgets.gantt_widget import GanttWidget
from taskdog.tui.widgets.task_table import TaskTable
from taskdog.view_models.task_view_model import TaskRowViewModel


class MainScreen(Screen[None]):
    """Main screen showing gantt chart and task list."""

    # Keep footer visible when a widget is maximized
    ALLOW_IN_MAXIMIZED_VIEW: ClassVar[str] = "#custom-footer"

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+j",
            "focus_next",
            "Next widget",
            show=False,
            priority=True,
            tooltip="Move focus to next focusable widget",
        ),
        Binding(
            "ctrl+k",
            "focus_previous",
            "Previous widget",
            show=False,
            priority=True,
            tooltip="Move focus to previous focusable widget",
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
        self.custom_footer: CustomFooter | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        # Header at the top
        yield Header(show_clock=True, id="main-header")

        with Vertical(id="root-container"):
            # Gantt chart section (main display)
            self.gantt_widget = GanttWidget(id="gantt-widget")
            self.gantt_widget.border_title = "Gantt Chart"
            yield self.gantt_widget

            # Task table (main content)
            self.task_table = TaskTable(id="task-table")  # type: ignore[no-untyped-call]
            self.task_table.border_title = "Tasks"
            yield self.task_table

        # Custom footer at screen level (full width)
        self.custom_footer = CustomFooter(id="custom-footer")
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

        Updates TUIState with the new query and posts FilterChanged
        to notify all widgets.

        Args:
            event: SearchQueryChanged event with the new query string
        """
        if self.state:
            self.state.set_filter(event.query)
            self.post_message(FilterChanged(query=event.query))

    def on_filter_changed(self, event: FilterChanged) -> None:
        """Handle filter state changes.

        Refreshes both TaskTable and GanttWidget with filtered data
        from TUIState.

        Args:
            event: FilterChanged event
        """
        # Refresh TaskTable with filtered viewmodels
        if self.task_table:
            self.task_table.render_filtered_tasks()

        # Refresh GanttWidget with filtered gantt
        if self.gantt_widget:
            self.gantt_widget.render_filtered_gantt()

        # Update search result count
        self._update_search_result()

    def on_custom_footer_submitted(self, event: CustomFooter.Submitted) -> None:
        """Handle Enter key press in search input.

        Args:
            event: CustomFooter submitted event
        """
        # Move focus back to the task table
        if self.task_table:
            self.task_table.focus()

    def on_custom_footer_refine_filter(self, event: CustomFooter.RefineFilter) -> None:
        """Handle Ctrl+R key press in search input to refine filter.

        Args:
            event: CustomFooter RefineFilter event
        """
        self._refine_filter()

    def _refine_filter(self) -> None:
        """Add current search query to filter chain for progressive filtering."""
        if not self.custom_footer or not self.state:
            return

        current_query = self.custom_footer.value
        if not current_query:
            return

        # Add current query to filter chain in TUIState
        self.state.add_to_filter_chain(current_query)

        # Clear search input for new query
        self.custom_footer.clear_input_only()

        # Update filter chain display
        self.custom_footer.update_filter_chain(self.state.filter_chain)

        # Post FilterChanged to refresh all widgets
        self.post_message(FilterChanged())

    def show_search(self) -> None:
        """Focus the search input."""
        if self.custom_footer:
            self.custom_footer.focus_input()

    def hide_search(self) -> None:
        """Clear the search filter and return focus to table."""
        if self.custom_footer:
            self.custom_footer.clear()

        # Clear filters in TUIState
        if self.state:
            self.state.clear_filters()

        # Post FilterChanged to refresh all widgets
        self.post_message(FilterChanged(is_cleared=True))

        if self.task_table:
            self.task_table.focus()

    def _update_search_result(self) -> None:
        """Update the search result count display."""
        if self.custom_footer and self.state:
            matched = self.state.match_count
            total = self.state.total_count
            self.custom_footer.update_result(matched, total)

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

    def get_explicitly_selected_task_ids(self) -> list[int]:
        """Get only explicitly selected task IDs (no cursor fallback)."""
        if self.task_table:
            return self.task_table.get_explicitly_selected_task_ids()
        return []

    def clear_task_selection(self) -> None:
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
