"""Task table widget for TUI."""

from typing import ClassVar

from textual.binding import Binding
from textual.widgets import DataTable

from domain.entities.task import Task
from presentation.constants.colors import STATUS_STYLES


class TaskTable(DataTable):
    """A data table widget for displaying tasks with Vi-style keyboard navigation."""

    # Add Vi-style bindings in addition to DataTable's default bindings
    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the task table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._task_map: dict[int, Task] = {}  # Maps row index to Task

    def setup_columns(self):
        """Set up table columns."""
        self.add_column("ID", width=6)
        self.add_column("Name", width=40)
        self.add_column("Priority", width=10)
        self.add_column("Status", width=15)
        self.add_column("Deadline", width=20)

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

            # Format deadline
            deadline = task.deadline if task.deadline else "-"

            # Add row
            self.add_row(
                str(task.id),
                task.name[:38] + "..." if len(task.name) > 38 else task.name,
                str(task.priority),
                status_styled,
                deadline,
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
