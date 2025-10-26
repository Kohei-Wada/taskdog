"""Task table widget for TUI."""

from datetime import datetime
from typing import ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.notes_repository import NotesRepository
from presentation.constants.colors import STATUS_STYLES
from presentation.constants.symbols import EMOJI_NOTE
from presentation.constants.table_dimensions import (
    DEADLINE_DISPLAY_LENGTH,
    PAGE_SCROLL_SIZE,
    TASK_NAME_MAX_DISPLAY_LENGTH,
    TASK_TABLE_DEADLINE_WIDTH,
    TASK_TABLE_DEPENDS_ON_WIDTH,
    TASK_TABLE_DURATION_WIDTH,
    TASK_TABLE_ELAPSED_WIDTH,
    TASK_TABLE_FIXED_WIDTH,
    TASK_TABLE_ID_WIDTH,
    TASK_TABLE_NAME_WIDTH,
    TASK_TABLE_NOTE_WIDTH,
    TASK_TABLE_PRIORITY_WIDTH,
    TASK_TABLE_STATUS_WIDTH,
    TASK_TABLE_TAGS_WIDTH,
)
from shared.constants.formats import DATETIME_FORMAT


class TaskTable(DataTable):
    """A data table widget for displaying tasks with Vi-style keyboard navigation."""

    # Add Vi-style bindings in addition to DataTable's default bindings
    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
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

    def setup_columns(self):
        """Set up table columns."""
        self.add_column(Text("ID", justify="center"), width=TASK_TABLE_ID_WIDTH)
        self.add_column(Text("Name", justify="center"), width=TASK_TABLE_NAME_WIDTH)
        self.add_column(Text("Pri", justify="center"), width=TASK_TABLE_PRIORITY_WIDTH)
        self.add_column(Text("Status", justify="center"), width=TASK_TABLE_STATUS_WIDTH)
        self.add_column(Text("Elapsed", justify="center"), width=TASK_TABLE_ELAPSED_WIDTH)
        self.add_column(Text("Fixed", justify="center"), width=TASK_TABLE_FIXED_WIDTH)
        self.add_column(Text("Deps", justify="center"), width=TASK_TABLE_DEPENDS_ON_WIDTH)
        self.add_column(Text("Duration", justify="center"), width=TASK_TABLE_DURATION_WIDTH)
        self.add_column(Text("Deadline", justify="center"), width=TASK_TABLE_DEADLINE_WIDTH)
        self.add_column(Text("Tags", justify="center"), width=TASK_TABLE_TAGS_WIDTH)
        self.add_column(Text("Note", justify="center"), width=TASK_TABLE_NOTE_WIDTH)

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
        self.clear()
        self._task_map.clear()

        for idx, task in enumerate(tasks):
            # Format status with color
            status_text = task.status.value
            status_color = STATUS_STYLES.get(task.status, "white")

            # Format duration
            duration = self._format_duration(task)

            # Format deadline
            deadline = self._format_deadline(task.deadline)

            # Format dependencies
            dependencies = self._format_dependencies(task)

            # Check if task has notes using NotesRepository
            note_indicator = EMOJI_NOTE if self.notes_repository.has_notes(task.id) else ""

            # Check if task is fixed
            fixed_indicator = "📌" if task.is_fixed else ""

            # Format elapsed time
            elapsed_time = self._format_elapsed_time(task)

            # Format name
            name_text = (
                task.name[:TASK_NAME_MAX_DISPLAY_LENGTH] + "..."
                if len(task.name) > TASK_NAME_MAX_DISPLAY_LENGTH
                else task.name
            )

            # Format tags
            tags_text = ", ".join(task.tags) if task.tags else ""
            if len(tags_text) > 18:
                tags_text = tags_text[:17] + "..."

            # Add row with centered Text objects
            self.add_row(
                Text(str(task.id), justify="center"),
                Text(name_text, justify="center"),
                Text(str(task.priority), justify="center"),
                Text(status_text, style=status_color, justify="center"),
                Text(elapsed_time, justify="center"),
                Text(fixed_indicator, justify="center"),
                Text(dependencies, justify="center"),
                Text(duration, justify="center"),
                Text(deadline, justify="center"),
                Text(tags_text, justify="center"),
                Text(note_indicator, justify="center"),
            )
            self._task_map[idx] = task

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
            filtered_tasks = self._filter_tasks(tasks, self._current_query)
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
            filtered_tasks = self._filter_tasks(self._all_tasks, query)
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

    def _filter_tasks(self, tasks: list[Task], query: str) -> list[Task]:
        """Filter tasks based on query using smart case matching.

        Smart case: case-insensitive if query is all lowercase,
        case-sensitive if query contains any uppercase.

        Args:
            tasks: List of tasks to filter
            query: Search query string

        Returns:
            List of tasks matching the query
        """
        # Smart case: case-sensitive if query has uppercase
        case_sensitive = any(c.isupper() for c in query)

        filtered = []
        for task in tasks:
            if self._task_matches_query(task, query, case_sensitive):
                filtered.append(task)

        return filtered

    def _task_matches_query(self, task: Task, query: str, case_sensitive: bool) -> bool:
        """Check if a task matches the search query.

        Searches across all visible fields: ID, name, status, priority,
        dependencies, duration, deadline, tags, and fixed status.

        Args:
            task: Task to check
            query: Search query string
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            True if task matches query, False otherwise
        """
        # Prepare query for comparison
        search_query = query if case_sensitive else query.lower()

        # Helper function to check if text contains query
        def matches(text: str) -> bool:
            if not text:
                return False
            search_text = text if case_sensitive else text.lower()
            return search_query in search_text

        # Build searchable fields
        searchable_fields = [
            str(task.id),
            task.name,
            task.status.value,
            str(task.priority),
            self._format_duration(task),
            self._format_deadline(task.deadline),
        ]

        # Add dependencies if present
        if task.depends_on:
            searchable_fields.append(",".join(str(dep_id) for dep_id in task.depends_on))

        # Add tags if present
        if task.tags:
            searchable_fields.extend(task.tags)

        # Add fixed indicators if task is fixed
        if task.is_fixed:
            searchable_fields.extend(["fixed", "📌"])

        # Check if query matches any field
        return any(matches(field) for field in searchable_fields)

    def action_scroll_home(self) -> None:
        """Move cursor to top (g key)."""
        if self.row_count > 0:
            self.move_cursor(row=0)

    def action_scroll_end(self) -> None:
        """Move cursor to bottom (G key)."""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)

    def action_page_down(self) -> None:
        """Move cursor down by half page (Ctrl+d)."""
        if self.row_count > 0:
            new_row = min(self.cursor_row + PAGE_SCROLL_SIZE, self.row_count - 1)
            self.move_cursor(row=new_row)

    def action_page_up(self) -> None:
        """Move cursor up by half page (Ctrl+u)."""
        if self.row_count > 0:
            new_row = max(self.cursor_row - PAGE_SCROLL_SIZE, 0)
            self.move_cursor(row=new_row)

    def _format_duration(self, task: Task) -> str:
        """Format duration information for display.

        Args:
            task: Task to format duration for

        Returns:
            Formatted duration string
        """
        if not task.estimated_duration and not task.actual_duration_hours:
            return "-"

        parts = []
        if task.estimated_duration:
            parts.append(f"E:{task.estimated_duration}h")
        if task.actual_duration_hours:
            parts.append(f"A:{task.actual_duration_hours}h")

        return " ".join(parts)

    def _format_dependencies(self, task: Task) -> str:
        """Format task dependencies for display.

        Args:
            task: Task to extract dependencies from

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not task.depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in task.depends_on)

    def _format_deadline(self, deadline: datetime | None) -> str:
        """Format deadline for display.

        Args:
            deadline: Deadline datetime object or None

        Returns:
            Formatted deadline string
        """
        if not deadline:
            return "-"
        # Format datetime to string, then show only date and time (YYYY-MM-DD HH:MM)
        deadline_str = deadline.strftime(DATETIME_FORMAT)
        if len(deadline_str) >= DEADLINE_DISPLAY_LENGTH:
            return deadline_str[:DEADLINE_DISPLAY_LENGTH]
        return deadline_str

    def _format_elapsed_time(self, task: Task) -> str:
        """Format elapsed time for IN_PROGRESS tasks.

        Args:
            task: Task to format elapsed time for

        Returns:
            Formatted elapsed time string (e.g., "15:04:38" or "3d 15:04:38")
        """
        if task.status != TaskStatus.IN_PROGRESS or not task.actual_start:
            return "-"

        # Calculate elapsed time
        elapsed_seconds = int((datetime.now() - task.actual_start).total_seconds())

        # Convert to days, hours, minutes, seconds
        days = elapsed_seconds // 86400
        remaining_seconds = elapsed_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        # Format based on duration
        if days > 0:
            return f"{days}d {hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
