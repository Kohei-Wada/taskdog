"""Task table widget for TUI.

This module provides a data table widget for displaying tasks with:
- Vi-style keyboard navigation
- Smart case search filtering
- Selection indicators
- Automatic formatting for all task fields
"""

from typing import TYPE_CHECKING, Any, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.widgets import DataTable

if TYPE_CHECKING:
    pass

from taskdog.constants.table_dimensions import PAGE_SCROLL_SIZE
from taskdog.tui.widgets.base_widget import TUIWidget
from taskdog.tui.widgets.task_table_row_builder import TaskTableRowBuilder
from taskdog.tui.widgets.vi_navigation_mixin import ViNavigationMixin
from taskdog.view_models.task_view_model import TaskRowViewModel


class TaskTable(DataTable, TUIWidget, ViNavigationMixin):  # type: ignore[type-arg]
    """A data table widget for displaying tasks with Vi-style keyboard navigation.

    This widget acts as a coordinator that delegates responsibilities to:
    - TaskSearchFilter: Handles search and filtering logic
    - TaskTableRowBuilder: Builds table row data from TaskRowViewModel
    - ViNavigationMixin: Provides Vi-style keybindings
    """

    # Add Vi-style bindings in addition to DataTable's default bindings
    BINDINGS: ClassVar = [
        # j/k navigation using DataTable's built-in cursor actions
        Binding(
            "j",
            "cursor_down",
            "Down",
            show=False,
            tooltip="Move cursor down (Vi-style)",
        ),
        Binding(
            "k", "cursor_up", "Up", show=False, tooltip="Move cursor up (Vi-style)"
        ),
        # g/G navigation for top/bottom
        Binding("g", "vi_home", "Top", show=False, tooltip="Jump to top (Vi-style)"),
        Binding(
            "G", "vi_end", "Bottom", show=False, tooltip="Jump to bottom (Vi-style)"
        ),
        # Vi-style page and horizontal scroll bindings from mixin
        *ViNavigationMixin.VI_PAGE_BINDINGS,
        *ViNavigationMixin.VI_HORIZONTAL_BINDINGS,
        *ViNavigationMixin.VI_HORIZONTAL_JUMP_BINDINGS,
        # Selection bindings
        Binding(
            "space",
            "toggle_selection",
            "Select",
            show=True,
            tooltip="Toggle selection for the current task",
        ),
        Binding(
            "ctrl+a",
            "select_all",
            "Select All",
            show=True,
            tooltip="Select all tasks in the table",
        ),
        Binding(
            "ctrl+n",
            "clear_selection",
            "Clear",
            show=True,
            tooltip="Clear all selections",
        ),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the task table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._viewmodel_map: dict[
            int, TaskRowViewModel
        ] = {}  # Maps row index to ViewModel
        # NOTE: Filter state moved to TUIState (Single Source of Truth)
        # - _current_query, _filter_chain, _search_filter removed
        self._selected_task_ids: set[int] = (
            set()
        )  # Selected task IDs for batch operations

        # Components
        self._row_builder = TaskTableRowBuilder()

    def setup_columns(self) -> None:
        """Set up table columns."""
        self.add_column(Text("", justify="center"))
        self.add_column(Text("ID", justify="center"))
        self.add_column(Text("Name", justify="center"))
        self.add_column(Text("Status", justify="center"))
        self.add_column(Text("Priority", justify="center"))
        self.add_column(Text("Flags", justify="center"))
        self.add_column(Text("Estimated[h]", justify="center"))
        self.add_column(Text("Actual[h]", justify="center"))
        self.add_column(Text("Deadline", justify="center"))
        self.add_column(Text("Planned Start", justify="center"))
        self.add_column(Text("Planned End", justify="center"))
        self.add_column(Text("Actual Start", justify="center"))
        self.add_column(Text("Actual End", justify="center"))
        self.add_column(Text("Elapsed", justify="center"))
        self.add_column(Text("Dependencies", justify="center"))
        self.add_column(Text("Tags", justify="center"))

    def load_tasks(self, view_models: list[TaskRowViewModel]) -> None:
        """Load task ViewModels into the table.

        Args:
            view_models: List of TaskRowViewModel to display (kept for API compatibility)
        """
        # NOTE: view_models parameter ignored - data is read from app.state (Step 5)
        # NOTE: Filter state is managed in TUIState, not cleared here
        self._render_tasks(self.tui_state.filtered_viewmodels)

    def _render_tasks(self, view_models: list[TaskRowViewModel]) -> None:
        """Render task ViewModels to the table using Textual's recommended pattern.

        Instead of clearing and rebuilding the entire table, this method:
        - Updates existing rows using update_cell_at() to preserve cursor and hover state
        - Adds new rows only when needed
        - Removes excess rows only when needed

        This approach maintains mouse hover state and cursor position automatically.

        Args:
            view_models: List of ViewModels to render
        """
        current_row_count = self.row_count
        new_row_count = len(view_models)

        # Update existing rows and add new ones
        for idx, task_vm in enumerate(view_models):
            # Build checkbox indicator
            checkbox = self._build_checkbox(task_vm.id)

            # Build row data using row builder with ViewModel
            row_data = self._row_builder.build_row(task_vm)

            if idx < current_row_count:
                # Update existing row using update_cell_at() - preserves cursor/hover state
                self.update_cell_at(Coordinate(idx, 0), checkbox)  # Checkbox column
                for col_idx, value in enumerate(row_data, start=1):
                    self.update_cell_at(Coordinate(idx, col_idx), value)
            else:
                # Add new row
                self.add_row(checkbox, *row_data)

            # Store ViewModel
            self._viewmodel_map[idx] = task_vm

        # Remove excess rows from the end
        while self.row_count > new_row_count:
            # Remove from viewmodel map first (before removing the row)
            row_idx_to_remove = self.row_count - 1
            if row_idx_to_remove in self._viewmodel_map:
                del self._viewmodel_map[row_idx_to_remove]
            # Get the last row key from coordinates and remove it
            # coordinate_to_cell_key returns (row_key, column_key)
            row_key, _ = self.coordinate_to_cell_key(Coordinate(row_idx_to_remove, 0))
            self.remove_row(row_key)

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
        """Get all (unfiltered) viewmodels from app state.

        Returns:
            List of TaskRowViewModel from state cache (unfiltered)
        """
        return self.tui_state.viewmodels_cache

    def refresh_tasks(
        self, view_models: list[TaskRowViewModel], keep_scroll_position: bool = False
    ) -> None:
        """Refresh the table with updated ViewModels while maintaining cursor position.

        Args:
            view_models: List of TaskRowViewModel to display (kept for API compatibility)
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        current_row = self.cursor_row
        # Save scroll position before refresh (both vertical and horizontal)
        # Note: scroll_y/scroll_x types from DataTable base class (type: ignore needed)
        saved_scroll_y: float | None = (
            self.scroll_y if keep_scroll_position else None  # type: ignore[has-type]
        )
        saved_scroll_x: float | None = (
            self.scroll_x if keep_scroll_position else None  # type: ignore[has-type]
        )

        # NOTE: view_models parameter ignored - data is read from app.state (Step 5)
        # Filter is applied by TUIState.filtered_viewmodels
        filtered_vms = self.tui_state.filtered_viewmodels

        self._render_tasks(filtered_vms)

        # Always restore cursor position if still valid
        if 0 <= current_row < len(self._viewmodel_map):
            self.move_cursor(row=current_row)

            # Restore scroll position to prevent stuttering
            if saved_scroll_y is not None:
                self.scroll_y = saved_scroll_y
            if saved_scroll_x is not None:
                self.scroll_x = saved_scroll_x

    def render_filtered_tasks(self) -> None:
        """Render tasks from TUIState.filtered_viewmodels.

        Called by MainScreen when filter state changes.
        """
        self._render_tasks(self.tui_state.filtered_viewmodels)

    # Legacy methods kept for backward compatibility
    # Filter state is now managed by TUIState

    def filter_tasks(self, query: str) -> None:
        """Filter task ViewModels based on search query.

        DEPRECATED: Use TUIState.set_filter() and post FilterChanged instead.
        This method is kept for backward compatibility.

        Args:
            query: Search query string
        """
        self.tui_state.set_filter(query)
        self._render_tasks(self.tui_state.filtered_viewmodels)

    def clear_filter(self) -> None:
        """Clear the current filter and filter chain, then show all ViewModels.

        DEPRECATED: Use TUIState.clear_filters() and post FilterChanged instead.
        This method is kept for backward compatibility.
        """
        self.tui_state.clear_filters()
        self._render_tasks(self.tui_state.filtered_viewmodels)

    @property
    def is_filtered(self) -> bool:
        """Check if a filter is currently active.

        Delegates to TUIState.is_filtered.
        """
        return self.tui_state.is_filtered

    @property
    def current_query(self) -> str:
        """Get the current search query.

        Delegates to TUIState.current_query.
        """
        return self.tui_state.current_query

    @property
    def filter_chain(self) -> list[str]:
        """Get the current filter chain.

        Delegates to TUIState.filter_chain.

        Returns:
            List of filter queries applied in order
        """
        return self.tui_state.filter_chain.copy()

    def add_filter_to_chain(self, query: str) -> None:
        """Add current query to filter chain for progressive filtering.

        DEPRECATED: Use TUIState.add_to_filter_chain() and post FilterChanged instead.
        This method is kept for backward compatibility.

        Args:
            query: Filter query to add to the chain
        """
        self.tui_state.add_to_filter_chain(query)

    def clear_filter_chain(self) -> None:
        """Clear all filters in the filter chain.

        DEPRECATED: Use TUIState.clear_filters() and post FilterChanged instead.
        This method is kept for backward compatibility.
        """
        self.tui_state.filter_chain.clear()

    @property
    def match_count(self) -> int:
        """Get the number of currently displayed (matched) tasks.

        Delegates to TUIState.match_count.
        """
        return self.tui_state.match_count

    @property
    def total_count(self) -> int:
        """Get the total number of tasks (unfiltered).

        Delegates to TUIState.total_count.
        """
        return self.tui_state.total_count

    @property
    def all_viewmodels(self) -> list[TaskRowViewModel]:
        """Get all loaded ViewModels (unfiltered).

        Returns:
            List of all TaskRowViewModel from app state cache
        """
        return self._get_all_viewmodels_from_state()

    def _safe_move_cursor(self, row: int) -> None:
        """Safely move cursor to specified row if table has rows.

        Args:
            row: Target row index
        """
        if self.row_count > 0:
            self.move_cursor(row=row)

    def action_vi_home(self) -> None:
        """Move cursor to top (g key)."""
        self._safe_move_cursor(row=0)

    def action_vi_end(self) -> None:
        """Move cursor to bottom (G key)."""
        self._safe_move_cursor(row=self.row_count - 1)

    def action_vi_page_down(self) -> None:
        """Move cursor down by half page (Ctrl+d)."""
        new_row = min(self.cursor_row + PAGE_SCROLL_SIZE, self.row_count - 1)
        self._safe_move_cursor(row=new_row)

    def action_vi_page_up(self) -> None:
        """Move cursor up by half page (Ctrl+u)."""
        new_row = max(self.cursor_row - PAGE_SCROLL_SIZE, 0)
        self._safe_move_cursor(row=new_row)

    def action_vi_scroll_left(self) -> None:
        """Scroll table left (h key)."""
        # Scroll left by one column width (approximate)
        scroll_amount = 10
        self.scroll_x = max(0, self.scroll_x - scroll_amount)

    def action_vi_scroll_right(self) -> None:
        """Scroll table right (l key)."""
        # Scroll right by one column width (approximate)
        scroll_amount = 10
        self.scroll_x = self.scroll_x + scroll_amount

    def action_vi_home_horizontal(self) -> None:
        """Scroll table to leftmost position (0 key)."""
        self.scroll_x = 0

    def action_vi_end_horizontal(self) -> None:
        """Scroll table to rightmost position ($ key)."""
        # Calculate maximum horizontal scroll position
        # virtual_size.width is the total content width
        # size.width is the visible viewport width
        max_scroll = max(0, self.virtual_size.width - self.size.width)
        self.scroll_x = max_scroll

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

        # Refresh only the current row to update checkbox
        self._refresh_current_row()

    def action_select_all(self) -> None:
        """Select all visible tasks (Ctrl+A)."""
        # Select all tasks in current view (respecting filter)
        for task_vm in self._viewmodel_map.values():
            self._selected_task_ids.add(task_vm.id)
        # Refresh table to show checkboxes
        self._render_tasks(list(self._viewmodel_map.values()))

    def action_clear_selection(self) -> None:
        """Clear all selections (Ctrl+N)."""
        self._selected_task_ids.clear()
        # Refresh table to hide checkboxes (uses filtered viewmodels from TUIState)
        self._render_tasks(self.tui_state.filtered_viewmodels)

    def _refresh_current_row(self) -> None:
        """Refresh only the current row to update checkbox display."""
        if self.cursor_row < 0 or self.cursor_row >= len(self._viewmodel_map):
            return

        task_vm = self._viewmodel_map[self.cursor_row]
        checkbox = self._build_checkbox(task_vm.id)

        # Update the checkbox cell
        self.update_cell_at(Coordinate(self.cursor_row, 0), checkbox)

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

    def get_explicitly_selected_task_ids(self) -> list[int]:
        """Get only explicitly selected task IDs (no cursor fallback).

        Unlike get_selected_task_ids(), this method does NOT fall back to
        the cursor position when no tasks are explicitly selected.
        Use this when you need to distinguish between "no selection" and
        "single task selected".

        Returns:
            List of explicitly selected task IDs, or empty list if none selected
        """
        return sorted(self._selected_task_ids) if self._selected_task_ids else []

    def clear_selection(self) -> None:
        """Clear all selections (called after batch operations)."""
        self._selected_task_ids.clear()
