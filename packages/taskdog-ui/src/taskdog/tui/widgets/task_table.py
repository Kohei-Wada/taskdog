"""Task table widget for TUI.

This module provides a data table widget for displaying tasks with:
- Vi-style keyboard navigation
- Smart case search filtering
- Selection indicators
- Automatic formatting for all task fields
"""

from typing import ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import DataTable

from taskdog.constants.table_dimensions import (
    PAGE_SCROLL_SIZE,
    TASK_TABLE_ACTUAL_END_WIDTH,
    TASK_TABLE_ACTUAL_START_WIDTH,
    TASK_TABLE_ACTUAL_WIDTH,
    TASK_TABLE_DEADLINE_WIDTH,
    TASK_TABLE_DEPENDS_ON_WIDTH,
    TASK_TABLE_ELAPSED_WIDTH,
    TASK_TABLE_EST_WIDTH,
    TASK_TABLE_FLAGS_WIDTH,
    TASK_TABLE_ID_WIDTH,
    TASK_TABLE_NAME_WIDTH,
    TASK_TABLE_PLANNED_END_WIDTH,
    TASK_TABLE_PLANNED_START_WIDTH,
    TASK_TABLE_PRIORITY_WIDTH,
    TASK_TABLE_STATUS_WIDTH,
    TASK_TABLE_TAGS_WIDTH,
)
from taskdog.tui.events import TaskSelected
from taskdog.tui.widgets.task_search_filter import TaskSearchFilter
from taskdog.tui.widgets.task_table_row_builder import TaskTableRowBuilder
from taskdog.view_models.task_view_model import TaskRowViewModel

# Checkbox column width
TASK_TABLE_CHECKBOX_WIDTH = 3


class TaskTable(DataTable):
    """A data table widget for displaying tasks with Vi-style keyboard navigation.

    This widget acts as a coordinator that delegates responsibilities to:
    - TaskSearchFilter: Handles search and filtering logic
    - TaskTableRowBuilder: Builds table row data from TaskRowViewModel
    """

    # Reactive variable for selection count (Phase 3)
    selection_count = reactive(0)

    # Add Vi-style bindings in addition to DataTable's default bindings
    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("ctrl+j", "cursor_down", "Down", show=False),
        Binding("ctrl+k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("h", "scroll_left", "Scroll Left", show=False),
        Binding("l", "scroll_right", "Scroll Right", show=False),
        Binding("space", "toggle_selection", "Select", show=True),
        Binding("ctrl+a", "select_all", "Select All", show=True),
        Binding("ctrl+n", "clear_selection", "Clear", show=True),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the task table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._viewmodel_map: dict[
            int, TaskRowViewModel
        ] = {}  # Maps row index to ViewModel
        # NOTE: _all_viewmodels removed - now accessed via self.app.state.viewmodels_cache (Step 5)
        self._current_query: str = ""  # Current search query
        self._selected_task_ids: set[int] = (
            set()
        )  # Selected task IDs for batch operations

        # Components
        self._search_filter = TaskSearchFilter()
        self._row_builder = TaskTableRowBuilder()

    def setup_columns(self):
        """Set up table columns."""
        self.add_column(Text("", justify="center"), width=TASK_TABLE_CHECKBOX_WIDTH)
        self.add_column(Text("ID", justify="center"), width=TASK_TABLE_ID_WIDTH)
        self.add_column(Text("Name", justify="center"), width=TASK_TABLE_NAME_WIDTH)
        self.add_column(Text("Status", justify="center"), width=TASK_TABLE_STATUS_WIDTH)
        self.add_column(Text("Pri", justify="center"), width=TASK_TABLE_PRIORITY_WIDTH)
        self.add_column(
            Text("Flag", justify="center"), width=TASK_TABLE_FLAGS_WIDTH
        )  # Flags (Fixed + Note)
        self.add_column(Text("Est", justify="center"), width=TASK_TABLE_EST_WIDTH)
        self.add_column(Text("Actual", justify="center"), width=TASK_TABLE_ACTUAL_WIDTH)
        self.add_column(
            Text("Deadline", justify="center"), width=TASK_TABLE_DEADLINE_WIDTH
        )
        self.add_column(
            Text("Plan Start", justify="center"), width=TASK_TABLE_PLANNED_START_WIDTH
        )
        self.add_column(
            Text("Plan End", justify="center"), width=TASK_TABLE_PLANNED_END_WIDTH
        )
        self.add_column(
            Text("Actual Start", justify="center"), width=TASK_TABLE_ACTUAL_START_WIDTH
        )
        self.add_column(
            Text("Actual End", justify="center"), width=TASK_TABLE_ACTUAL_END_WIDTH
        )
        self.add_column(
            Text("Elapsed", justify="center"), width=TASK_TABLE_ELAPSED_WIDTH
        )
        self.add_column(
            Text("Deps", justify="center"), width=TASK_TABLE_DEPENDS_ON_WIDTH
        )
        self.add_column(Text("Tags", justify="center"), width=TASK_TABLE_TAGS_WIDTH)

    def load_tasks(self, view_models: list[TaskRowViewModel]):
        """Load task ViewModels into the table.

        Args:
            view_models: List of TaskRowViewModel to display (kept for API compatibility)
        """
        # NOTE: view_models parameter ignored - data is read from app.state (Step 5)
        self._current_query = ""
        self._render_tasks(self._get_all_viewmodels_from_state())

    def _render_tasks(self, view_models: list[TaskRowViewModel]):
        """Render task ViewModels to the table.

        Args:
            view_models: List of ViewModels to render
        """
        self.clear()
        self._viewmodel_map.clear()

        for idx, task_vm in enumerate(view_models):
            # Build checkbox indicator
            checkbox = self._build_checkbox(task_vm.id)

            # Build row data using row builder with ViewModel
            row_data = self._row_builder.build_row(task_vm)

            # Add checkbox as first column, then other columns
            self.add_row(checkbox, *row_data)
            # Store ViewModel
            self._viewmodel_map[idx] = task_vm

    def _build_checkbox(self, task_id: int) -> Text:
        """Build checkbox indicator for a task.

        Args:
            task_id: Task ID to check selection status

        Returns:
            Rich Text object with checkbox indicator
        """
        if task_id in self._selected_task_ids:
            return Text("󰱒")
        return Text("󰄱")

    def get_selected_task_id(self) -> int | None:
        """Get the ID of the currently selected task.

        Returns:
            The selected task ID, or None if no task is selected
        """
        vm = self.get_selected_task_vm()
        return vm.id if vm else None

    def get_selected_task_vm(self) -> TaskRowViewModel | None:
        """Get the currently selected task as a ViewModel.

        Returns:
            The selected TaskRowViewModel, or None if no task is selected
        """
        if self.cursor_row < 0 or self.cursor_row >= len(self._viewmodel_map):
            return None
        return self._viewmodel_map.get(self.cursor_row)

    def _get_all_viewmodels_from_state(self) -> list[TaskRowViewModel]:
        """Get all viewmodels from app state.

        Returns:
            List of all TaskRowViewModel from app state cache
        """
        from taskdog.tui.app import TaskdogTUI

        app = self.app
        assert isinstance(app, TaskdogTUI)
        return app.state.viewmodels_cache

    def refresh_tasks(
        self, view_models: list[TaskRowViewModel], keep_scroll_position: bool = False
    ):
        """Refresh the table with updated ViewModels while maintaining cursor position.

        Args:
            view_models: List of TaskRowViewModel to display (kept for API compatibility)
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        current_row = self.cursor_row
        # Save scroll position before refresh (both vertical and horizontal)
        saved_scroll_y = self.scroll_y if keep_scroll_position else None
        saved_scroll_x = self.scroll_x if keep_scroll_position else None

        # NOTE: view_models parameter ignored - data is read from app.state (Step 5)
        all_viewmodels = self._get_all_viewmodels_from_state()
        # Reapply current filter if active
        if self._current_query:
            filtered_vms = self._search_filter.filter(
                all_viewmodels, self._current_query
            )
            self._render_tasks(filtered_vms)
        else:
            self._render_tasks(all_viewmodels)

        # Always restore cursor position if still valid
        if 0 <= current_row < len(self._viewmodel_map):
            self.move_cursor(row=current_row)

            # Restore scroll position to prevent stuttering
            if saved_scroll_y is not None:
                self.scroll_y = saved_scroll_y
            if saved_scroll_x is not None:
                self.scroll_x = saved_scroll_x

    def filter_tasks(self, query: str):
        """Filter task ViewModels based on search query with smart case matching.

        Args:
            query: Search query string
        """
        self._current_query = query
        all_viewmodels = self._get_all_viewmodels_from_state()
        if not query:
            # No filter - show all ViewModels
            self._render_tasks(all_viewmodels)
        else:
            filtered_vms = self._search_filter.filter(all_viewmodels, query)
            self._render_tasks(filtered_vms)

    def clear_filter(self):
        """Clear the current filter and show all ViewModels."""
        self._current_query = ""
        self._render_tasks(self._get_all_viewmodels_from_state())

    @property
    def is_filtered(self) -> bool:
        """Check if a filter is currently active."""
        return bool(self._current_query)

    @property
    def current_query(self) -> str:
        """Get the current search query."""
        return self._current_query

    @property
    def match_count(self) -> int:
        """Get the number of currently displayed (matched) tasks."""
        return len(self._viewmodel_map)

    @property
    def total_count(self) -> int:
        """Get the total number of tasks (unfiltered)."""
        return len(self._get_all_viewmodels_from_state())

    @property
    def all_viewmodels(self) -> list[TaskRowViewModel]:
        """Get all loaded ViewModels (unfiltered).

        Returns:
            List of all TaskRowViewModel from app state cache
        """
        return self._get_all_viewmodels_from_state()

    def watch_cursor_row(self, old_row: int, new_row: int) -> None:
        """Called when cursor row changes.

        Posts a TaskSelected event to notify other widgets of the selection change.

        Args:
            old_row: Previous cursor row index
            new_row: New cursor row index
        """
        # Get the currently selected task ID
        selected_task_id = self.get_selected_task_id()
        # Post TaskSelected event for other widgets to react
        self.post_message(TaskSelected(selected_task_id))

    def _safe_move_cursor(self, row: int) -> None:
        """Safely move cursor to specified row if table has rows.

        Args:
            row: Target row index
        """
        if self.row_count > 0:
            self.move_cursor(row=row)

    def action_scroll_home(self) -> None:
        """Move cursor to top (g key)."""
        self._safe_move_cursor(row=0)

    def action_scroll_end(self) -> None:
        """Move cursor to bottom (G key)."""
        self._safe_move_cursor(row=self.row_count - 1)

    def action_page_down(self) -> None:
        """Move cursor down by half page (Ctrl+d)."""
        new_row = min(self.cursor_row + PAGE_SCROLL_SIZE, self.row_count - 1)
        self._safe_move_cursor(row=new_row)

    def action_page_up(self) -> None:
        """Move cursor up by half page (Ctrl+u)."""
        new_row = max(self.cursor_row - PAGE_SCROLL_SIZE, 0)
        self._safe_move_cursor(row=new_row)

    def action_scroll_left(self) -> None:
        """Scroll table left (h key)."""
        # Scroll left by one column width (approximate)
        scroll_amount = 10
        self.scroll_x = max(0, self.scroll_x - scroll_amount)

    def action_scroll_right(self) -> None:
        """Scroll table right (l key)."""
        # Scroll right by one column width (approximate)
        scroll_amount = 10
        self.scroll_x = self.scroll_x + scroll_amount

    # Multi-selection actions
    def action_toggle_selection(self) -> None:
        """Toggle selection for current row (Space key)."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            return

        if task_id in self._selected_task_ids:
            self._selected_task_ids.remove(task_id)
        else:
            self._selected_task_ids.add(task_id)

        # Update reactive variable (automatically triggers watch_selection_count)
        self.selection_count = len(self._selected_task_ids)

        # Refresh only the current row to update checkbox
        self._refresh_current_row()

    def action_select_all(self) -> None:
        """Select all visible tasks (Ctrl+A)."""
        # Select all tasks in current view (respecting filter)
        for task_vm in self._viewmodel_map.values():
            self._selected_task_ids.add(task_vm.id)
        # Update reactive variable
        self.selection_count = len(self._selected_task_ids)
        # Refresh table to show checkboxes
        self._render_tasks(list(self._viewmodel_map.values()))

    def action_clear_selection(self) -> None:
        """Clear all selections (Ctrl+N)."""
        self._selected_task_ids.clear()
        # Update reactive variable
        self.selection_count = 0
        # Refresh table to hide checkboxes
        all_viewmodels = self._get_all_viewmodels_from_state()
        if self._current_query:
            filtered_vms = self._search_filter.filter(
                all_viewmodels, self._current_query
            )
            self._render_tasks(filtered_vms)
        else:
            self._render_tasks(all_viewmodels)

    def _refresh_current_row(self) -> None:
        """Refresh only the current row to update checkbox display."""
        if self.cursor_row < 0 or self.cursor_row >= len(self._viewmodel_map):
            return

        task_vm = self._viewmodel_map[self.cursor_row]
        checkbox = self._build_checkbox(task_vm.id)

        # Update the checkbox cell
        self.update_cell_at((self.cursor_row, 0), checkbox)

    def get_selected_task_ids(self) -> list[int]:
        """Get all selected task IDs for batch operations.

        If no tasks are selected, returns current cursor position task ID.
        This maintains backward compatibility with single-task operations.

        Returns:
            List of selected task IDs, or [current_task_id] if none selected
        """
        if self._selected_task_ids:
            return sorted(self._selected_task_ids)

        # Fall back to single selection (cursor position)
        task_id = self.get_selected_task_id()
        return [task_id] if task_id else []

    def clear_selection(self) -> None:
        """Clear all selections (called after batch operations)."""
        self._selected_task_ids.clear()
        # Update reactive variable
        self.selection_count = 0
