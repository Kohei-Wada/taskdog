"""Tests for TableCellBuilder."""

import unittest

from rich.text import Text

from taskdog.builders.table_cell_builder import TableCellBuilder


class TestTableCellBuilder(unittest.TestCase):
    """Test cases for TableCellBuilder."""

    def test_build_centered_cell_with_string(self):
        """Test build_centered_cell with a string value."""
        result = TableCellBuilder.build_centered_cell("Test")
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Test")
        self.assertEqual(result.justify, "center")

    def test_build_centered_cell_with_int(self):
        """Test build_centered_cell with an integer value."""
        result = TableCellBuilder.build_centered_cell(42)
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "42")
        self.assertEqual(result.justify, "center")

    def test_build_left_aligned_cell_without_style(self):
        """Test build_left_aligned_cell without style."""
        result = TableCellBuilder.build_left_aligned_cell("Left Text")
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Left Text")
        self.assertEqual(result.justify, "left")

    def test_build_left_aligned_cell_with_style(self):
        """Test build_left_aligned_cell with style."""
        result = TableCellBuilder.build_left_aligned_cell("Styled Text", style="bold")
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Styled Text")
        self.assertEqual(result.justify, "left")
        # Check that style was applied by checking spans
        self.assertTrue(len(result._spans) > 0, "Style should be applied via spans")

    def test_build_styled_cell_default_center(self):
        """Test build_styled_cell with default center justification."""
        result = TableCellBuilder.build_styled_cell("Center", style="italic")
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Center")
        self.assertEqual(result.justify, "center")
        # Check that style was applied by checking spans
        self.assertTrue(len(result._spans) > 0, "Style should be applied via spans")

    def test_build_styled_cell_right_justified(self):
        """Test build_styled_cell with right justification."""
        result = TableCellBuilder.build_styled_cell("Right", justify="right")
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Right")
        self.assertEqual(result.justify, "right")

    def test_build_cell_from_formatter(self):
        """Test build_cell_from_formatter with formatter function."""

        def sample_formatter(value: int) -> str:
            return f"{value}h"

        result = TableCellBuilder.build_cell_from_formatter(sample_formatter, 8)
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "8h")
        self.assertEqual(result.justify, "center")

    def test_build_cell_from_formatter_multiple_args(self):
        """Test build_cell_from_formatter with multiple arguments."""

        def multi_arg_formatter(prefix: str, value: int, suffix: str) -> str:
            return f"{prefix}{value}{suffix}"

        result = TableCellBuilder.build_cell_from_formatter(
            multi_arg_formatter, "Task ", 5, " hours"
        )
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, "Task 5 hours")
        self.assertEqual(result.justify, "center")


if __name__ == "__main__":
    unittest.main()
