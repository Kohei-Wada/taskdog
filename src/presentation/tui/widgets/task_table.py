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
from textual.widgets import DataTable

from domain.entities.task import Task
from infrastructure.persistence.notes_repository import NotesRepository
from presentation.constants.table_dimensions import (
    PAGE_SCROLL_SIZE,
    TASK_TABLE_DEADLINE_WIDTH,
    TASK_TABLE_DEPENDS_ON_WIDTH,
    TASK_TABLE_DURATION_WIDTH,
    TASK_TABLE_ELAPSED_WIDTH,
    TASK_TABLE_FLAGS_WIDTH,
    TASK_TABLE_ID_WIDTH,
    TASK_TABLE_NAME_WIDTH,
    TASK_TABLE_PRIORITY_WIDTH,
    TASK_TABLE_STATUS_WIDTH,
    TASK_TABLE_TAGS_WIDTH,
)
from presentation.tui.widgets.cursor_indicator_manager import CursorIndicatorManager
from presentation.tui.widgets.task_search_filter import TaskSearchFilter
from presentation.tui.widgets.task_table_row_builder import TaskTableRowBuilder


class TaskTable(DataTable):
    """A data table widget for displaying tasks with Vi-style keyboard navigation.

    This widget acts as a coordinator that delegates responsibilities to:
    - TaskSearchFilter: Handles search and filtering logic
    - TaskTableRowBuilder: Builds table row data from Task entities
    - CursorIndicatorManager: Manages the selection indicator
    """

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
    ]

    def __init__(self, notes_repository: NotesRepository, *args, **kwargs):
        """Initialize the task table.

        Args:
            notes_repository: Notes repository for checking note existence
        """
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._task_map: dict[int, Task] = {}  # Maps row index to Task
        self.notes_repository = notes_repository
        self._all_tasks: list[Task] = []  # All tasks (unfiltered)
        self._current_query: str = ""  # Current search query

        # Components
        self._search_filter = TaskSearchFilter()
        self._row_builder = TaskTableRowBuilder(notes_repository)
        self._indicator_manager = CursorIndicatorManager(self)

    def setup_columns(self):
        """Set up table columns."""
        self.add_column(Text("", justify="center"), width=2, key="indicator")
        self.add_column(Text("ID", justify="center"), width=TASK_TABLE_ID_WIDTH)
        self.add_column(Text("Name", justify="center"), width=TASK_TABLE_NAME_WIDTH)
        self.add_column(Text("Pri", justify="center"), width=TASK_TABLE_PRIORITY_WIDTH)
        self.add_column(Text("Status", justify="center"), width=TASK_TABLE_STATUS_WIDTH)
        self.add_column(Text("Elapsed", justify="center"), width=TASK_TABLE_ELAPSED_WIDTH)
        self.add_column(Text("Duration", justify="center"), width=TASK_TABLE_DURATION_WIDTH)
        self.add_column(Text("Deadline", justify="center"), width=TASK_TABLE_DEADLINE_WIDTH)
        self.add_column(Text("Deps", justify="center"), width=TASK_TABLE_DEPENDS_ON_WIDTH)
        self.add_column(Text("Tags", justify="center"), width=TASK_TABLE_TAGS_WIDTH)
        self.add_column(
            Text("", justify="center"), width=TASK_TABLE_FLAGS_WIDTH
        )  # Flags (Fixed + Note)

    def load_tasks(self, tasks: list[Task]):
        """Load tasks into the table.

        Args:
            tasks: List of tasks to display
        """
        self._all_tasks = tasks
        self._current_query = ""
        self._render_tasks(tasks)

    def _render_tasks(self, tasks: list[Task]):
        """Render tasks to the table.

        Args:
            tasks: List of tasks to render
        """
        # Save current cursor position before clearing
        saved_cursor_row = self.cursor_row if self.row_count > 0 else 0

        self.clear()
        self._task_map.clear()
        self._indicator_manager.clear()

        for idx, task in enumerate(tasks):
            # Build row data using row builder
            is_selected = idx == saved_cursor_row
            row_data = self._row_builder.build_row(task, is_selected)

            # Add row and register with indicator manager
            row_key = self.add_row(*row_data)
            self._task_map[idx] = task
            self._indicator_manager.set_row_key(idx, row_key)

        # Set initial indicator position
        if saved_cursor_row >= 0 and saved_cursor_row < len(self._task_map):
            self._indicator_manager.set_initial_indicator(saved_cursor_row)

    def get_selected_task(self) -> Task | None:
        """Get the currently selected task.

        Returns:
            The selected Task, or None if no task is selected
        """
        if self.cursor_row < 0 or self.cursor_row >= len(self._task_map):
            return None
        return self._task_map.get(self.cursor_row)

    def refresh_tasks(self, tasks: list[Task], keep_scroll_position: bool = False):
        """Refresh the table with updated tasks while maintaining cursor position.

        Args:
            tasks: List of tasks to display
            keep_scroll_position: Whether to preserve scroll position during refresh.
                                 Set to True for periodic updates to avoid scroll stuttering.
        """
        current_row = self.cursor_row
        # Save scroll position before refresh
        saved_scroll_y = self.scroll_y if keep_scroll_position else None

        self._all_tasks = tasks
        # Reapply current filter if active
        if self._current_query:
            filtered_tasks = self._search_filter.filter(tasks, self._current_query)
            self._render_tasks(filtered_tasks)
        else:
            self._render_tasks(tasks)

        # Always restore cursor position if still valid
        if 0 <= current_row < len(self._task_map):
            self.move_cursor(row=current_row)

            # Restore scroll position to prevent stuttering
            if saved_scroll_y is not None:
                self.scroll_y = saved_scroll_y

    def filter_tasks(self, query: str):
        """Filter tasks based on search query with smart case matching.

        Args:
            query: Search query string
        """
        self._current_query = query
        if not query:
            # No filter - show all tasks
            self._render_tasks(self._all_tasks)
        else:
            filtered_tasks = self._search_filter.filter(self._all_tasks, query)
            self._render_tasks(filtered_tasks)

    def clear_filter(self):
        """Clear the current filter and show all tasks."""
        self._current_query = ""
        self._render_tasks(self._all_tasks)

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
        return len(self._task_map)

    @property
    def total_count(self) -> int:
        """Get the total number of tasks (unfiltered)."""
        return len(self._all_tasks)

    def action_cursor_down(self) -> None:
        """Override cursor down to update indicator."""
        super().action_cursor_down()
        self._update_indicator()

    def action_cursor_up(self) -> None:
        """Override cursor up to update indicator."""
        super().action_cursor_up()
        self._update_indicator()

    def action_scroll_home(self) -> None:
        """Move cursor to top (g key)."""
        if self.row_count > 0:
            self.move_cursor(row=0)
            self._update_indicator()

    def action_scroll_end(self) -> None:
        """Move cursor to bottom (G key)."""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)
            self._update_indicator()

    def action_page_down(self) -> None:
        """Move cursor down by half page (Ctrl+d)."""
        if self.row_count > 0:
            new_row = min(self.cursor_row + PAGE_SCROLL_SIZE, self.row_count - 1)
            self.move_cursor(row=new_row)
            self._update_indicator()

    def action_page_up(self) -> None:
        """Move cursor up by half page (Ctrl+u)."""
        if self.row_count > 0:
            new_row = max(self.cursor_row - PAGE_SCROLL_SIZE, 0)
            self.move_cursor(row=new_row)
            self._update_indicator()

    def _update_indicator(self) -> None:
        """Update the selection indicator for the current cursor position."""
        self._indicator_manager.update_indicator(self.cursor_row)
