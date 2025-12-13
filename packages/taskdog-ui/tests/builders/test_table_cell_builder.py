"""Tests for TableCellBuilder."""

import pytest
from rich.text import Text

from taskdog.builders.table_cell_builder import TableCellBuilder


class TestTableCellBuilder:
    """Test cases for TableCellBuilder."""

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
