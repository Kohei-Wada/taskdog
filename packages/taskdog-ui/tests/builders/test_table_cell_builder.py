"""Tests for TableCellBuilder."""

import unittest

from parameterized import parameterized
from rich.text import Text

from taskdog.builders.table_cell_builder import TableCellBuilder


class TestTableCellBuilder(unittest.TestCase):
    """Test cases for TableCellBuilder."""

    @parameterized.expand(
        [
            ("string_value", "Test", "Test"),
            ("int_value", 42, "42"),
        ]
    )
    def test_build_centered_cell(self, scenario, value, expected_plain):
        """Test build_centered_cell with different value types."""
        result = TableCellBuilder.build_centered_cell(value)
        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, expected_plain)
        self.assertEqual(result.justify, "center")

    @parameterized.expand(
        [
            ("without_style", "Left Text", None, False),
            ("with_style", "Styled Text", "bold", True),
        ]
    )
    def test_build_left_aligned_cell(self, scenario, text, style, should_have_style):
        """Test build_left_aligned_cell with and without style."""
        if style:
            result = TableCellBuilder.build_left_aligned_cell(text, style=style)
        else:
            result = TableCellBuilder.build_left_aligned_cell(text)

        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, text)
        self.assertEqual(result.justify, "left")

        if should_have_style:
            self.assertTrue(len(result._spans) > 0, "Style should be applied via spans")

    @parameterized.expand(
        [
            ("default_center", "Center", "italic", "center"),
            ("right_justified", "Right", None, "right"),
        ]
    )
    def test_build_styled_cell(self, scenario, text, style, justify):
        """Test build_styled_cell with different justifications."""
        if justify == "right":
            result = TableCellBuilder.build_styled_cell(text, justify=justify)
        else:
            result = TableCellBuilder.build_styled_cell(text, style=style)

        self.assertIsInstance(result, Text)
        self.assertEqual(result.plain, text)
        self.assertEqual(result.justify, justify)

        if style:
            self.assertTrue(len(result._spans) > 0, "Style should be applied via spans")

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
