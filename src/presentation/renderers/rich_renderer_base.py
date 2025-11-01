"""Base class for Rich-based task renderers."""

from io import StringIO

from rich.console import Console
from rich.table import Table
from rich.text import Text

from domain.entities.task import TaskStatus
from presentation.constants.colors import STATUS_COLORS_BOLD, STATUS_STYLES
from presentation.renderers.task_renderer import TaskRenderer


class RichRendererBase(TaskRenderer):
    """Base class for renderers using Rich library.

    Provides common utility methods for Rich-based rendering,
    including status styling and table rendering.
    """

    def _get_status_style(self, status: TaskStatus) -> str:
        """Get Rich style for a task status.

        Args:
            status: Task status

        Returns:
            Rich style string (e.g., "yellow", "blue", "green", "red")
        """
        return STATUS_STYLES.get(status.value, "white")

    def _get_status_color(self, status: TaskStatus) -> str:
        """Get color for status bar in Gantt chart.

        Args:
            status: Task status

        Returns:
            Color string with bold modifier for Gantt charts
        """
        return STATUS_COLORS_BOLD.get(status.value, "white")

    def _render_to_string(
        self, table: Table, footer: Text | None = None, width: int | None = None
    ) -> str:
        """Render a Rich table to string with optional footer.

        Args:
            table: Rich Table to render
            footer: Optional footer text to append after table
            width: Optional console width

        Returns:
            Rendered string with ANSI codes
        """
        string_io = StringIO()
        console_kwargs = {"file": string_io, "force_terminal": True}
        if width:
            console_kwargs["width"] = width

        console = Console(**console_kwargs)
        console.print(table)

        if footer:
            console.print()
            console.print(footer)

        return string_io.getvalue().rstrip()
