"""Tests for CommaSeparatedSuggester."""

import pytest

from taskdog.tui.forms.suggesters.comma_separated_suggester import (
    CommaSeparatedSuggester,
)


class TestCommaSeparatedSuggester:
    """Tests for CommaSeparatedSuggester."""

    @pytest.fixture
    def suggester(self):
        return CommaSeparatedSuggester(["work", "urgent", "client-a", "client-b"])

    @pytest.mark.asyncio
    async def test_basic_prefix_match(self, suggester):
        """Single input matching the start of a suggestion."""
        result = await suggester.get_suggestion("wo")
        assert result == "work"

    @pytest.mark.asyncio
    async def test_basic_prefix_match_another(self, suggester):
        result = await suggester.get_suggestion("ur")
        assert result == "urgent"

    @pytest.mark.asyncio
    async def test_no_match(self, suggester):
        """No suggestion matches the input."""
        result = await suggester.get_suggestion("xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_input(self, suggester):
        """Empty input returns None."""
        result = await suggester.get_suggestion("")
        assert result is None

    @pytest.mark.asyncio
    async def test_comma_separated_last_segment(self, suggester):
        """Completes only the last segment after a comma."""
        result = await suggester.get_suggestion("work,ur")
        assert result == "work,urgent"

    @pytest.mark.asyncio
    async def test_comma_separated_with_spaces(self, suggester):
        """Handles spaces after comma in the last segment."""
        result = await suggester.get_suggestion("work, ur")
        assert result == "work, urgent"

    @pytest.mark.asyncio
    async def test_excludes_already_entered_tags(self, suggester):
        """Tags already entered are excluded from suggestions."""
        # "client-a" is already entered, so "cl" should match "client-b"
        result = await suggester.get_suggestion("client-a,cl")
        assert result == "client-a,client-b"

    @pytest.mark.asyncio
    async def test_excludes_multiple_entered_tags(self, suggester):
        """Multiple entered tags are all excluded."""
        result = await suggester.get_suggestion("client-a,client-b,cl")
        assert result is None

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, suggester):
        """Matching is case insensitive (value is casefolded by Suggester base)."""
        result = await suggester.get_suggestion("wo")
        assert result == "work"

    @pytest.mark.asyncio
    async def test_case_insensitive_exclusion(self, suggester):
        """Entered tags are excluded case-insensitively."""
        suggester_mixed = CommaSeparatedSuggester(["Work", "urgent"])
        # "work" entered (casefolded), should exclude "Work" suggestion
        result = await suggester_mixed.get_suggestion("work,wo")
        assert result is None

    @pytest.mark.asyncio
    async def test_exact_match_single(self, suggester):
        """Exact full match of a suggestion returns it."""
        result = await suggester.get_suggestion("work")
        assert result == "work"

    @pytest.mark.asyncio
    async def test_comma_then_empty(self, suggester):
        """Trailing comma with no input returns None."""
        result = await suggester.get_suggestion("work,")
        assert result is None

    @pytest.mark.asyncio
    async def test_comma_then_space_only(self, suggester):
        """Trailing comma with only spaces returns None."""
        result = await suggester.get_suggestion("work, ")
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_commas(self, suggester):
        """Works with multiple comma-separated values."""
        result = await suggester.get_suggestion("work,urgent,cl")
        assert result == "work,urgent,client-a"

    @pytest.mark.asyncio
    async def test_empty_suggestions_list(self):
        """Empty suggestions list always returns None."""
        suggester = CommaSeparatedSuggester([])
        result = await suggester.get_suggestion("wo")
        assert result is None

    @pytest.mark.asyncio
    async def test_first_matching_suggestion_returned(self):
        """Returns the first matching suggestion in order."""
        suggester = CommaSeparatedSuggester(["alpha", "alpha-2", "beta"])
        result = await suggester.get_suggestion("al")
        assert result == "alpha"
