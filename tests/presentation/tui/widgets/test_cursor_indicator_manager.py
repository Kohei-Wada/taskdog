"""Tests for CursorIndicatorManager."""

import unittest
from unittest.mock import MagicMock, call

from presentation.tui.widgets.cursor_indicator_manager import CursorIndicatorManager


class TestCursorIndicatorManager(unittest.TestCase):
    """Test CursorIndicatorManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_table = MagicMock()
        self.manager = CursorIndicatorManager(self.data_table)

    def test_initialization(self):
        """Test manager initialization."""
        self.assertEqual(self.manager._previous_cursor_row, -1)
        self.assertEqual(len(self.manager._row_keys), 0)

    def test_set_row_key(self):
        """Test setting row keys."""
        row_key1 = "row_key_1"
        row_key2 = "row_key_2"

        self.manager.set_row_key(0, row_key1)
        self.manager.set_row_key(1, row_key2)

        self.assertEqual(self.manager._row_keys[0], row_key1)
        self.assertEqual(self.manager._row_keys[1], row_key2)

    def test_clear(self):
        """Test clearing row keys and cursor position."""
        self.manager.set_row_key(0, "row_key_1")
        self.manager.set_row_key(1, "row_key_2")
        self.manager._previous_cursor_row = 1

        self.manager.clear()

        self.assertEqual(len(self.manager._row_keys), 0)
        self.assertEqual(self.manager._previous_cursor_row, -1)

    def test_update_indicator_first_time(self):
        """Test updating indicator for the first time (no previous indicator)."""
        row_key = "row_key_0"
        self.manager.set_row_key(0, row_key)

        self.manager.update_indicator(0)

        # Should set indicator at row 0
        self.data_table.update_cell.assert_called_once_with(row_key, "indicator", ">")
        self.assertEqual(self.manager._previous_cursor_row, 0)

    def test_update_indicator_clears_previous(self):
        """Test that updating indicator clears the previous one."""
        row_key_0 = "row_key_0"
        row_key_1 = "row_key_1"
        self.manager.set_row_key(0, row_key_0)
        self.manager.set_row_key(1, row_key_1)

        # Set initial indicator at row 0
        self.manager.update_indicator(0)
        self.data_table.update_cell.reset_mock()

        # Move to row 1
        self.manager.update_indicator(1)

        # Should clear row 0 and set row 1
        calls = self.data_table.update_cell.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], call(row_key_0, "indicator", ""))  # Clear previous
        self.assertEqual(calls[1], call(row_key_1, "indicator", ">"))  # Set new

        self.assertEqual(self.manager._previous_cursor_row, 1)

    def test_update_indicator_invalid_row(self):
        """Test updating indicator with invalid row (not in _row_keys)."""
        self.manager.set_row_key(0, "row_key_0")

        # Try to update to row 5 (not registered)
        self.manager.update_indicator(5)

        # Should not call update_cell
        self.data_table.update_cell.assert_not_called()

    def test_update_indicator_negative_row(self):
        """Test updating indicator with negative row."""
        self.manager.set_row_key(0, "row_key_0")
        self.manager.update_indicator(0)
        self.data_table.update_cell.reset_mock()

        # Try to update to row -1
        self.manager.update_indicator(-1)

        # Should only clear previous (row 0), but not set new indicator
        self.data_table.update_cell.assert_called_once_with("row_key_0", "indicator", "")

    def test_set_initial_indicator(self):
        """Test setting initial indicator."""
        row_key = "row_key_2"
        self.manager.set_row_key(2, row_key)

        self.manager.set_initial_indicator(2)

        # Should only track the position, not update the cell
        # (indicator is set during row building)
        self.assertEqual(self.manager._previous_cursor_row, 2)
        self.data_table.update_cell.assert_not_called()

    def test_set_initial_indicator_invalid_row(self):
        """Test setting initial indicator with invalid row."""
        self.manager.set_initial_indicator(5)  # Not registered

        # Should not change previous cursor row
        self.assertEqual(self.manager._previous_cursor_row, -1)

    def test_multiple_updates(self):
        """Test multiple indicator updates."""
        for i in range(5):
            self.manager.set_row_key(i, f"row_key_{i}")

        # Move through rows: 0 -> 1 -> 2 -> 1 -> 0
        positions = [0, 1, 2, 1, 0]
        for pos in positions:
            self.manager.update_indicator(pos)

        # Final position should be 0
        self.assertEqual(self.manager._previous_cursor_row, 0)

        # Verify last call set indicator at row 0
        last_call = self.data_table.update_cell.call_args_list[-1]
        self.assertEqual(last_call, call("row_key_0", "indicator", ">"))


if __name__ == "__main__":
    unittest.main()
