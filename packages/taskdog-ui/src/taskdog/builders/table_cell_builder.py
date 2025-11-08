"""Table cell building utilities."""

from collections.abc import Callable
from typing import Literal

from rich.text import Text


class TableCellBuilder:
    """Builds Rich Text objects for table cells.

    Provides utilities for creating consistently formatted table cells
    with proper justification and styling.
    """

    @staticmethod
    def build_centered_cell(value: str | int) -> Text:
        """Create a centered text cell.

        Args:
            value: Value to display in the cell

        Returns:
            Text object with centered justification
        """
        return Text(str(value), justify="center")

    @staticmethod
    def build_left_aligned_cell(value: str, style: str | None = None) -> Text:
        """Create a left-aligned text cell.

        Args:
            value: Value to display in the cell
            style: Optional Rich style string (e.g., "bold", "strike")

        Returns:
            Text object with left justification
        """
        # Rich Text expects style as str or None (handled internally)
        text = Text(value, justify="left")
        if style:
            text.stylize(style)
        return text

    @staticmethod
    def build_styled_cell(
        value: str,
        style: str | None = None,
        justify: Literal["default", "left", "center", "right", "full"] = "center",
    ) -> Text:
        """Create a styled text cell with custom justification.

        Args:
            value: Value to display in the cell
            style: Optional Rich style string
            justify: Text justification ("left", "center", "right", "full", "default")

        Returns:
            Text object with specified style and justification
        """
        text = Text(value, justify=justify)
        if style:
            text.stylize(style)
        return text

    @staticmethod
    def build_cell_from_formatter(
        formatter_func: Callable[..., str], *args: object
    ) -> Text:
        """Create a cell using a formatter function.

        Args:
            formatter_func: Formatter function to call (returns str)
            *args: Arguments to pass to the formatter

        Returns:
            Text object with centered justification
        """
        return Text(formatter_func(*args), justify="center")
