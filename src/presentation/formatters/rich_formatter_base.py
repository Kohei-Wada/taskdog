"""Base class for Rich-based task formatters."""

from typing import Optional
from io import StringIO
from rich.console import Console
from rich.table import Table
from rich.text import Text
from domain.entities.task import TaskStatus
from presentation.formatters.task_formatter import TaskFormatter
from presentation.formatters.constants import STATUS_STYLES, STATUS_COLORS_BOLD


class RichFormatterBase(TaskFormatter):
    """Base class for formatters using Rich library.

    Provides common utility methods for Rich-based formatting,
    including status styling and table rendering.
    """

    def _get_status_style(self, status: TaskStatus) -> str:
        """Get Rich style for a task status.

        Args:
            status: Task status

        Returns:
            Rich style string (e.g., "yellow", "blue", "green", "red")
        """
        return STATUS_STYLES.get(status, "white")

    def _get_status_color(self, status: TaskStatus) -> str:
        """Get color for status bar in Gantt chart.

        Args:
            status: Task status

        Returns:
            Color string with bold modifier for Gantt charts
        """
        return STATUS_COLORS_BOLD.get(status, "white")

    def _render_to_string(
        self, table: Table, footer: Optional[Text] = None, width: Optional[int] = None
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
