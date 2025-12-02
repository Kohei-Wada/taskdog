"""Tests for TableCellBuilder."""

import pytest
from rich.text import Text

from taskdog.builders.table_cell_builder import TableCellBuilder


class TestTableCellBuilder:
    """Test cases for TableCellBuilder."""

    @pytest.mark.parametrize(
        "value,expected_plain",
        [
            ("Test", "Test"),
            (42, "42"),
        ],
        ids=["string_value", "int_value"],
    )
    def test_build_centered_cell(self, value, expected_plain):
        """Test build_centered_cell with different value types."""
        result = TableCellBuilder.build_centered_cell(value)
        assert isinstance(result, Text)
        assert result.plain == expected_plain
        assert result.justify == "center"

    @pytest.mark.parametrize(
        "text,style,should_have_style",
        [
            ("Left Text", None, False),
            ("Styled Text", "bold", True),
        ],
        ids=["without_style", "with_style"],
    )
    def test_build_left_aligned_cell(self, text, style, should_have_style):
        """Test build_left_aligned_cell with and without style."""
        if style:
            result = TableCellBuilder.build_left_aligned_cell(text, style=style)
        else:
            result = TableCellBuilder.build_left_aligned_cell(text)

        assert isinstance(result, Text)
        assert result.plain == text
        assert result.justify == "left"

        if should_have_style:
            assert len(result._spans) > 0, "Style should be applied via spans"

    @pytest.mark.parametrize(
        "text,style,justify",
        [
            ("Center", "italic", "center"),
            ("Right", None, "right"),
        ],
        ids=["default_center", "right_justified"],
    )
    def test_build_styled_cell(self, text, style, justify):
        """Test build_styled_cell with different justifications."""
        if justify == "right":
            result = TableCellBuilder.build_styled_cell(text, justify=justify)
        else:
            result = TableCellBuilder.build_styled_cell(text, style=style)

        assert isinstance(result, Text)
        assert result.plain == text
        assert result.justify == justify

        if style:
            assert len(result._spans) > 0, "Style should be applied via spans"

    def test_build_cell_from_formatter(self):
        """Test build_cell_from_formatter with formatter function."""

        def sample_formatter(value: int) -> str:
            return f"{value}h"

        result = TableCellBuilder.build_cell_from_formatter(sample_formatter, 8)
        assert isinstance(result, Text)
        assert result.plain == "8h"
        assert result.justify == "center"

    def test_build_cell_from_formatter_multiple_args(self):
        """Test build_cell_from_formatter with multiple arguments."""

        def multi_arg_formatter(prefix: str, value: int, suffix: str) -> str:
            return f"{prefix}{value}{suffix}"

        result = TableCellBuilder.build_cell_from_formatter(
            multi_arg_formatter, "Task ", 5, " hours"
        )
        assert isinstance(result, Text)
        assert result.plain == "Task 5 hours"
        assert result.justify == "center"
