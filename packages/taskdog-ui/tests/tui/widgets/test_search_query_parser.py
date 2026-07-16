"""Tests for SearchQueryParser."""

import pytest

from taskdog.tui.widgets.search_query_parser import (
    SearchQueryParser,
    SearchToken,
    TokenType,
)


class TestSearchQueryParser:
    """Test SearchQueryParser parsing functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.parser = SearchQueryParser()

    def test_parse_empty_query(self):
        """Test parsing empty query returns empty list."""
        tokens = self.parser.parse("")
        assert tokens == []

    def test_parse_whitespace_only_query(self):
        """Test parsing whitespace-only query returns empty list."""
        tokens = self.parser.parse("   ")
        assert tokens == []

    def test_parse_simple_term(self):
        """Test parsing simple term returns INCLUDE token."""
        tokens = self.parser.parse("bug")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.INCLUDE, value="bug")

    def test_parse_multiple_terms(self):
        """Test parsing multiple terms returns multiple INCLUDE tokens."""
        tokens = self.parser.parse("bug fix")
        assert len(tokens) == 2
        assert tokens[0] == SearchToken(type=TokenType.INCLUDE, value="bug")
        assert tokens[1] == SearchToken(type=TokenType.INCLUDE, value="fix")

    def test_parse_exclude_term(self):
        """Test parsing !term returns EXCLUDE token."""
        tokens = self.parser.parse("!bug")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE, value="bug")

    def test_parse_exclude_completed_shorthand(self):
        """Test parsing !completed returns EXCLUDE_STATUS with is_finished."""
        tokens = self.parser.parse("!completed")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="is_finished"
        )

    def test_parse_exclude_pending_shorthand(self):
        """Test parsing !pending returns EXCLUDE_STATUS with PENDING."""
        tokens = self.parser.parse("!pending")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE_STATUS, value="PENDING")

    def test_parse_exclude_in_progress_shorthand(self):
        """Test parsing !in_progress returns EXCLUDE_STATUS with IN_PROGRESS."""
        tokens = self.parser.parse("!in_progress")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="IN_PROGRESS"
        )

    def test_parse_exclude_canceled_shorthand(self):
        """Test parsing !canceled returns EXCLUDE_STATUS with CANCELED."""
        tokens = self.parser.parse("!canceled")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE_STATUS, value="CANCELED")

    def test_parse_exclude_status_explicit(self):
        """Test parsing !status:VALUE returns EXCLUDE_STATUS token."""
        tokens = self.parser.parse("!status:COMPLETED")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="COMPLETED"
        )

    def test_parse_exclude_status_case_insensitive(self):
        """Test parsing !status:value is case-insensitive for prefix."""
        tokens = self.parser.parse("!STATUS:COMPLETED")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="COMPLETED"
        )

    def test_parse_exclude_tag(self):
        """Test parsing !tag:tagname returns EXCLUDE_TAG token."""
        tokens = self.parser.parse("!tag:urgent")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE_TAG, value="urgent")

    def test_parse_exclude_tag_case_insensitive_prefix(self):
        """Test parsing !TAG:tagname is case-insensitive for prefix."""
        tokens = self.parser.parse("!TAG:urgent")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE_TAG, value="urgent")

    def test_parse_mixed_include_and_exclude(self):
        """Test parsing mixed include and exclude terms."""
        tokens = self.parser.parse("bug !completed")
        assert len(tokens) == 2
        assert tokens[0] == SearchToken(type=TokenType.INCLUDE, value="bug")
        assert tokens[1] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="is_finished"
        )

    def test_parse_complex_query(self):
        """Test parsing complex query with multiple token types."""
        tokens = self.parser.parse("auth !completed !tag:urgent")
        assert len(tokens) == 3
        assert tokens[0] == SearchToken(type=TokenType.INCLUDE, value="auth")
        assert tokens[1] == SearchToken(
            type=TokenType.EXCLUDE_STATUS, value="is_finished"
        )
        assert tokens[2] == SearchToken(type=TokenType.EXCLUDE_TAG, value="urgent")

    def test_parse_exclamation_only(self):
        """Test parsing lone ! returns empty list (fzf: empty exclusion = all match)."""
        tokens = self.parser.parse("!")
        assert len(tokens) == 0

    def test_parse_exclamation_with_space(self):
        """Test parsing ! followed by space skips the ! token."""
        tokens = self.parser.parse("! bug")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.INCLUDE, value="bug")

    def test_parse_preserves_case_for_values(self):
        """Test that values preserve their original case."""
        tokens = self.parser.parse("BugFix")
        assert tokens[0].value == "BugFix"

    def test_parse_exclude_preserves_case_for_values(self):
        """Test that exclude values preserve their original case."""
        tokens = self.parser.parse("!BugFix")
        assert tokens[0].value == "BugFix"

    def test_parse_multiple_spaces_between_terms(self):
        """Test parsing with multiple spaces between terms."""
        tokens = self.parser.parse("bug    fix")
        assert len(tokens) == 2
        assert tokens[0].value == "bug"
        assert tokens[1].value == "fix"

    def test_parse_exclude_status_without_value(self):
        """Test parsing !status: without value treats as literal exclude."""
        tokens = self.parser.parse("!status:")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE, value="status:")

    def test_parse_exclude_tag_without_value(self):
        """Test parsing !tag: without value treats as literal exclude."""
        tokens = self.parser.parse("!tag:")
        assert len(tokens) == 1
        assert tokens[0] == SearchToken(type=TokenType.EXCLUDE, value="tag:")


class TestSearchToken:
    """Test SearchToken dataclass."""

    def test_token_equality(self):
        """Test SearchToken equality."""
        token1 = SearchToken(type=TokenType.INCLUDE, value="bug")
        token2 = SearchToken(type=TokenType.INCLUDE, value="bug")
        assert token1 == token2

    def test_token_inequality_different_type(self):
        """Test SearchToken inequality with different types."""
        token1 = SearchToken(type=TokenType.INCLUDE, value="bug")
        token2 = SearchToken(type=TokenType.EXCLUDE, value="bug")
        assert token1 != token2

    def test_token_inequality_different_value(self):
        """Test SearchToken inequality with different values."""
        token1 = SearchToken(type=TokenType.INCLUDE, value="bug")
        token2 = SearchToken(type=TokenType.INCLUDE, value="fix")
        assert token1 != token2

    def test_token_is_frozen(self):
        """Test SearchToken is immutable."""
        token = SearchToken(type=TokenType.INCLUDE, value="bug")
        with pytest.raises(AttributeError):
            token.value = "new"


class TestTokenType:
    """Test TokenType enum."""

    def test_token_types_exist(self):
        """Test all expected token types exist."""
        assert TokenType.INCLUDE
        assert TokenType.EXCLUDE
        assert TokenType.EXCLUDE_STATUS
        assert TokenType.EXCLUDE_TAG
