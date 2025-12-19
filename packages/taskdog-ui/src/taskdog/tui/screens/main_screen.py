"""Main screen for the TUI."""

from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header

from taskdog.tui.events import SearchQueryChanged
from taskdog.tui.state import TUIState
from taskdog.tui.widgets.audit_log_widget import AuditLogWidget
from taskdog.tui.widgets.custom_footer import CustomFooter
from taskdog.tui.widgets.gantt_widget import GanttWidget
from taskdog.tui.widgets.task_table import TaskTable
from taskdog.view_models.task_view_model import TaskRowViewModel

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


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
        self.audit_widget: AuditLogWidget | None = None
        self._audit_panel_visible: bool = False

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Returns:
            Iterable of widgets to display
        """
        # Header at the top
        yield Header(show_clock=True, id="main-header")

        with Horizontal(id="root-container"):
            # Left side: main content
            with Vertical(id="left-content"):
                # Gantt chart section (main display)
                self.gantt_widget = GanttWidget(id="gantt-widget")
                self.gantt_widget.border_title = "Gantt Chart"
                yield self.gantt_widget

                # Task table (main content)
                self.task_table = TaskTable(id="task-table")  # type: ignore[no-untyped-call]
                self.task_table.border_title = "Tasks"
                yield self.task_table

            # Right side: Audit log panel (full height, hidden by default)
            self.audit_widget = AuditLogWidget(id="audit-panel")
            yield self.audit_widget

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

        Args:
            event: SearchQueryChanged event with the new query string
        """
        # Filter tasks based on search query
        if self.task_table:
            self.task_table.filter_tasks(event.query)
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
        if not self.custom_footer or not self.task_table:
            return

        current_query = self.custom_footer.value
        if not current_query:
            return

        # Add current query to filter chain
        self.task_table.add_filter_to_chain(current_query)

        # Clear search input for new query
        self.custom_footer.clear_input_only()

        # Update filter chain display
        filter_chain = self.task_table.filter_chain
        self.custom_footer.update_filter_chain(filter_chain)

        # Reapply filters to show refined results
        self.task_table.filter_tasks("")

        # Update search result count
        self._update_search_result()

    def show_search(self) -> None:
        """Focus the search input."""
        if self.custom_footer:
            self.custom_footer.focus_input()

    def hide_search(self) -> None:
        """Clear the search filter and return focus to table."""
        if self.custom_footer:
            self.custom_footer.clear()

        if self.task_table:
            self.task_table.clear_filter()  # type: ignore[no-untyped-call]
            self.task_table.focus()

    def _update_search_result(self) -> None:
        """Update the search result count display."""
        if self.custom_footer and self.task_table:
            matched = self.task_table.match_count
            total = self.task_table.total_count
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

    # Audit panel methods

    def toggle_audit_panel(self) -> None:
        """Toggle the visibility of the audit log panel."""
        if not self.audit_widget:
            return

        self._audit_panel_visible = not self._audit_panel_visible

        if self._audit_panel_visible:
            self.audit_widget.add_class("visible")
            self._load_initial_audit_logs()
        else:
            self.audit_widget.remove_class("visible")

    def _load_initial_audit_logs(self) -> None:
        """Load recent audit logs via API when panel is opened."""
        try:
            tui_app: TaskdogTUI = self.app  # type: ignore[assignment]
            result = tui_app.api_client.list_audit_logs(limit=30)
            if self.audit_widget:
                self.audit_widget.load_logs(result.logs)
        except Exception as e:
            self.app.notify(f"Failed to load audit logs: {e}", severity="error")

    def refresh_audit_panel(self) -> None:
        """Refresh audit logs if panel is visible.

        Called by WebSocket event handlers when task events occur.
        """
        if not self._audit_panel_visible or not self.audit_widget:
            return

        try:
            tui_app: TaskdogTUI = self.app  # type: ignore[assignment]
            result = tui_app.api_client.list_audit_logs(limit=30)
            self.audit_widget.load_logs(result.logs)
        except Exception as e:
            self.app.notify(f"Failed to refresh audit logs: {e}", severity="error")

    @property
    def is_audit_panel_visible(self) -> bool:
        """Check if audit panel is currently visible.

        Returns:
            True if audit panel is visible
        """
        return self._audit_panel_visible
