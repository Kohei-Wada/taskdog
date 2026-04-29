"""Tests for text_formatter."""

import pytest

from taskdog.formatters.text_formatter import format_finished_name


class TestFormatFinishedName:
    """Test cases for format_finished_name."""

    @pytest.mark.parametrize(
        "name,is_finished,expected",
        [
            ("Task A", False, "Task A"),
            ("Task A", True, "[strike dim]Task A[/strike dim]"),
        ],
        ids=["unfinished", "finished"],
    )
    def test_format_finished_name(self, name, is_finished, expected):
        result = format_finished_name(name, is_finished)
        assert result == expected

    def test_escapes_rich_markup_when_unfinished(self):
        result = format_finished_name("[tracker] Task", False)
        assert result == r"\[tracker] Task"

    def test_escapes_rich_markup_when_finished(self):
        result = format_finished_name("[tracker] Task", True)
        assert result == r"[strike dim]\[tracker] Task[/strike dim]"
