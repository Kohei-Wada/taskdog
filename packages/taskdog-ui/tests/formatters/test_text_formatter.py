"""Tests for text_formatter."""

import pytest

from taskdog.constants.symbols import EMOJI_FIXED, EMOJI_NOTE
from taskdog.formatters.text_formatter import (
    EMPTY_FIELD_PLACEHOLDER,
    format_dependencies,
    format_finished_name,
    format_flags,
    format_tags,
)


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


class TestFormatTags:
    """Test cases for format_tags."""

    @pytest.mark.parametrize(
        "tags,expected",
        [
            (None, EMPTY_FIELD_PLACEHOLDER),
            ([], EMPTY_FIELD_PLACEHOLDER),
            (["solo"], "solo"),
            (["urgent", "backend"], "urgent, backend"),
        ],
        ids=["none", "empty", "single", "multiple"],
    )
    def test_format_tags(self, tags, expected):
        assert format_tags(tags) == expected


class TestFormatDependencies:
    """Test cases for format_dependencies."""

    @pytest.mark.parametrize(
        "depends_on,expected",
        [
            (None, EMPTY_FIELD_PLACEHOLDER),
            ([], EMPTY_FIELD_PLACEHOLDER),
            ([10], "10"),
            ([1, 3], "1,3"),
        ],
        ids=["none", "empty", "single", "multiple"],
    )
    def test_format_dependencies(self, depends_on, expected):
        assert format_dependencies(depends_on) == expected


class TestFormatFlags:
    """Test cases for format_flags."""

    @pytest.mark.parametrize(
        "is_fixed,has_notes,expected",
        [
            (False, False, ""),
            (True, False, EMOJI_FIXED),
            (False, True, EMOJI_NOTE),
            (True, True, EMOJI_FIXED + EMOJI_NOTE),
        ],
        ids=["none", "fixed_only", "notes_only", "both"],
    )
    def test_format_flags(self, is_fixed, has_notes, expected):
        assert format_flags(is_fixed, has_notes) == expected
