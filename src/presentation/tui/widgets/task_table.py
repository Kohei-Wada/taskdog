"""Task table widget for TUI."""

from typing import ClassVar

from textual.binding import Binding
from textual.widgets import DataTable

from domain.entities.task import Task
from presentation.constants.colors import STATUS_STYLES
from presentation.constants.symbols import EMOJI_NOTE
from presentation.constants.table_dimensions import (
    DEADLINE_DISPLAY_LENGTH,
    PAGE_SCROLL_SIZE,
    TASK_NAME_MAX_DISPLAY_LENGTH,
    TASK_TABLE_DEADLINE_WIDTH,
    TASK_TABLE_DEPENDS_ON_WIDTH,
    TASK_TABLE_DURATION_WIDTH,
    TASK_TABLE_FIXED_WIDTH,
    TASK_TABLE_ID_WIDTH,
    TASK_TABLE_NAME_WIDTH,
    TASK_TABLE_NOTE_WIDTH,
    TASK_TABLE_PRIORITY_WIDTH,
    TASK_TABLE_STATUS_WIDTH,
)


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

    def __init__(self, *args, **kwargs):
        """Initialize the task table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._task_map: dict[int, Task] = {}  # Maps row index to Task

    def setup_columns(self):
        """Set up table columns."""
        self.add_column("ID", width=TASK_TABLE_ID_WIDTH)
        self.add_column("Name", width=TASK_TABLE_NAME_WIDTH)
        self.add_column("Pri", width=TASK_TABLE_PRIORITY_WIDTH)
        self.add_column("Status", width=TASK_TABLE_STATUS_WIDTH)
        self.add_column("Fixed", width=TASK_TABLE_FIXED_WIDTH)
        self.add_column("Deps", width=TASK_TABLE_DEPENDS_ON_WIDTH)
        self.add_column("Duration", width=TASK_TABLE_DURATION_WIDTH)
        self.add_column("Deadline", width=TASK_TABLE_DEADLINE_WIDTH)
        self.add_column("Note", width=TASK_TABLE_NOTE_WIDTH)

    def load_tasks(self, tasks: list[Task]):
        """Load tasks into the table.

        Args:
            tasks: List of tasks to display
        """
        self.clear()
        self._task_map.clear()

        for idx, task in enumerate(tasks):
            # Format status with color
            status_text = task.status.value
            status_color = STATUS_STYLES.get(task.status, "white")
            status_styled = f"[{status_color}]{status_text}[/{status_color}]"

            # Format duration
            duration = self._format_duration(task)

            # Format deadline
            deadline = self._format_deadline(task.deadline)

            # Format dependencies
            dependencies = self._format_dependencies(task)

            # Check if task has notes
            note_indicator = EMOJI_NOTE if task.has_note else ""

            # Check if task is fixed
            fixed_indicator = "📌" if task.is_fixed else ""

            # Add row
            self.add_row(
                str(task.id),
                (
                    task.name[:TASK_NAME_MAX_DISPLAY_LENGTH] + "..."
                    if len(task.name) > TASK_NAME_MAX_DISPLAY_LENGTH
                    else task.name
                ),
                str(task.priority),
                status_styled,
                fixed_indicator,
                dependencies,
                duration,
                deadline,
                note_indicator,
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

    def refresh_tasks(self, tasks: list[Task]):
        """Refresh the table with updated tasks while maintaining cursor position.

        Args:
            tasks: List of tasks to display
        """
        current_row = self.cursor_row
        self.load_tasks(tasks)
        # Restore cursor position if still valid
        if 0 <= current_row < len(self._task_map):
            self.move_cursor(row=current_row)

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

    def _format_deadline(self, deadline: str | None) -> str:
        """Format deadline for display.

        Args:
            deadline: Deadline string or None

        Returns:
            Formatted deadline string
        """
        if not deadline:
            return "-"
        # Show only date and time (YYYY-MM-DD HH:MM)
        if len(deadline) >= DEADLINE_DISPLAY_LENGTH:
            return deadline[:DEADLINE_DISPLAY_LENGTH]
        return deadline
