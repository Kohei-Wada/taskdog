"""Cursor indicator manager for task table."""

from textual.widgets import DataTable


class CursorIndicatorManager:
    """Manages the cursor position indicator in a DataTable.

    Handles the display of a selection indicator (">") at the current
    cursor position and clearing it when the cursor moves.
    """

    def __init__(self, data_table: DataTable):
        """Initialize the cursor indicator manager.

        Args:
            data_table: DataTable widget to manage indicators for
        """
        self.data_table = data_table
        self._row_keys: dict[int, object] = {}  # Maps row index to row key
        self._previous_cursor_row: int = -1  # Track previous cursor position

    def set_row_key(self, row_index: int, row_key: object) -> None:
        """Register a row key for a given row index.

        Args:
            row_index: Index of the row
            row_key: DataTable row key object
        """
        self._row_keys[row_index] = row_key

    def clear(self) -> None:
        """Clear all tracked row keys and reset cursor position."""
        self._row_keys.clear()
        self._previous_cursor_row = -1

    def update_indicator(self, current_row: int) -> None:
        """Update the selection indicator for the current cursor position.

        Clears the indicator at the previous cursor position and sets it
        at the new position.

        Args:
            current_row: Current cursor row index
        """
        # Clear previous indicator if valid
        if self._previous_cursor_row >= 0 and self._previous_cursor_row in self._row_keys:
            prev_row_key = self._row_keys[self._previous_cursor_row]
            self.data_table.update_cell(prev_row_key, "indicator", "")

        # Set new indicator if valid
        if current_row >= 0 and current_row in self._row_keys:
            row_key = self._row_keys[current_row]
            self.data_table.update_cell(row_key, "indicator", ">")
            self._previous_cursor_row = current_row

    def set_initial_indicator(self, row_index: int) -> None:
        """Set the initial indicator at a specific row index.

        Used when rendering tasks to set the indicator at the saved cursor position.

        Args:
            row_index: Row index to set indicator at
        """
        if row_index >= 0 and row_index in self._row_keys:
            self._previous_cursor_row = row_index
