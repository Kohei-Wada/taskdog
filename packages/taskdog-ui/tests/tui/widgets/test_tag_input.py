"""Tests for TagInput widget."""

from taskdog.tui.widgets.tag_input import TagInput


class TestGetCurrentFragment:
    """Tests for TagInput._get_current_fragment()."""

    def test_empty_input(self) -> None:
        """Empty input returns empty fragment."""
        widget = TagInput(value="", id="test")
        assert widget._get_current_fragment() == ""

    def test_single_word_in_progress(self) -> None:
        """Single word being typed returns that word."""
        widget = TagInput(value="wor", id="test")
        assert widget._get_current_fragment() == "wor"

    def test_after_comma_empty(self) -> None:
        """After a comma with nothing typed returns empty."""
        widget = TagInput(value="work,", id="test")
        assert widget._get_current_fragment() == ""

    def test_after_comma_with_space(self) -> None:
        """After a comma with space returns empty."""
        widget = TagInput(value="work, ", id="test")
        assert widget._get_current_fragment() == ""

    def test_after_comma_typing(self) -> None:
        """After a comma with text returns the text."""
        widget = TagInput(value="work,urg", id="test")
        assert widget._get_current_fragment() == "urg"

    def test_multiple_tags_typing(self) -> None:
        """Multiple completed tags plus typing returns last fragment."""
        widget = TagInput(value="work,urgent,cli", id="test")
        assert widget._get_current_fragment() == "cli"

    def test_spaces_stripped(self) -> None:
        """Whitespace around fragment is stripped."""
        widget = TagInput(value="work, urg ", id="test")
        assert widget._get_current_fragment() == "urg"


class TestGetCompletedTags:
    """Tests for TagInput._get_completed_tags()."""

    def test_no_comma_returns_empty(self) -> None:
        """No comma means no completed tags."""
        widget = TagInput(value="work", id="test")
        assert widget._get_completed_tags() == []

    def test_one_completed_tag(self) -> None:
        """One tag followed by comma."""
        widget = TagInput(value="work,", id="test")
        assert widget._get_completed_tags() == ["work"]

    def test_multiple_completed_tags(self) -> None:
        """Multiple completed tags."""
        widget = TagInput(value="work,urgent,client", id="test")
        assert widget._get_completed_tags() == ["work", "urgent"]

    def test_tags_lowercased(self) -> None:
        """Completed tags are lowercased for comparison."""
        widget = TagInput(value="Work,Urgent,", id="test")
        assert widget._get_completed_tags() == ["work", "urgent"]

    def test_empty_parts_skipped(self) -> None:
        """Empty parts from consecutive commas are skipped."""
        widget = TagInput(value="work,,urgent,", id="test")
        assert widget._get_completed_tags() == ["work", "urgent"]


class TestFilterSuggestions:
    """Tests for TagInput._filter_suggestions()."""

    def test_empty_fragment_returns_all(self) -> None:
        """Empty fragment returns all available tags."""
        widget = TagInput(available_tags=["work", "urgent", "client"], id="test")
        result = widget._filter_suggestions("")
        assert result == ["work", "urgent", "client"]

    def test_prefix_match(self) -> None:
        """Fragment filters by prefix match."""
        widget = TagInput(available_tags=["work", "urgent", "weekend"], id="test")
        result = widget._filter_suggestions("wo")
        assert result == ["work"]

    def test_case_insensitive_match(self) -> None:
        """Matching is case-insensitive."""
        widget = TagInput(available_tags=["Work", "URGENT", "client"], id="test")
        result = widget._filter_suggestions("ur")
        assert result == ["URGENT"]

    def test_excludes_already_entered(self) -> None:
        """Tags already entered are excluded from suggestions."""
        widget = TagInput(
            available_tags=["work", "urgent", "client"],
            value="work,",
            id="test",
        )
        result = widget._filter_suggestions("")
        assert result == ["urgent", "client"]

    def test_no_match_returns_empty(self) -> None:
        """No matching tags returns empty list."""
        widget = TagInput(available_tags=["work", "urgent"], id="test")
        result = widget._filter_suggestions("xyz")
        assert result == []

    def test_no_available_tags(self) -> None:
        """No available tags returns empty list."""
        widget = TagInput(available_tags=[], id="test")
        result = widget._filter_suggestions("wo")
        assert result == []

    def test_none_available_tags(self) -> None:
        """None available tags returns empty list."""
        widget = TagInput(id="test")
        result = widget._filter_suggestions("wo")
        assert result == []

    def test_exact_match_excluded_when_completed(self) -> None:
        """Exact match of completed tag is excluded."""
        widget = TagInput(
            available_tags=["work", "workout"],
            value="work,wo",
            id="test",
        )
        result = widget._filter_suggestions("wo")
        assert result == ["workout"]


class TestIsValid:
    """Tests for TagInput.is_valid property."""

    def test_empty_is_valid(self) -> None:
        """Empty input is valid (tags are optional)."""
        widget = TagInput(value="", id="test")
        assert widget.is_valid is True

    def test_single_tag_valid(self) -> None:
        """Single alphanumeric tag is valid."""
        widget = TagInput(value="work", id="test")
        assert widget.is_valid is True

    def test_tag_with_hyphen_valid(self) -> None:
        """Tag with hyphen is valid."""
        widget = TagInput(value="client-a", id="test")
        assert widget.is_valid is True

    def test_tag_with_underscore_valid(self) -> None:
        """Tag with underscore is valid."""
        widget = TagInput(value="my_tag", id="test")
        assert widget.is_valid is True

    def test_multiple_tags_valid(self) -> None:
        """Multiple comma-separated tags are valid."""
        widget = TagInput(value="work,urgent,client-a", id="test")
        assert widget.is_valid is True

    def test_trailing_comma_valid(self) -> None:
        """Trailing comma is valid (mid-input state)."""
        widget = TagInput(value="work,", id="test")
        assert widget.is_valid is True

    def test_spaces_around_comma_valid(self) -> None:
        """Spaces around commas are valid."""
        widget = TagInput(value="work , urgent", id="test")
        assert widget.is_valid is True

    def test_invalid_characters(self) -> None:
        """Tags with invalid characters are invalid."""
        widget = TagInput(value="work@home", id="test")
        assert widget.is_valid is False

    def test_space_in_tag_invalid(self) -> None:
        """Spaces within a tag name are invalid."""
        widget = TagInput(value="my tag", id="test")
        assert widget.is_valid is False


class TestTagInputInitialization:
    """Tests for TagInput initialization."""

    def test_default_values(self) -> None:
        """Default initialization has empty values."""
        widget = TagInput(id="test")
        assert widget._initial_value == ""
        assert widget._available_tags == []

    def test_with_available_tags(self) -> None:
        """Tags are stored from constructor."""
        tags = ["work", "urgent"]
        widget = TagInput(available_tags=tags, id="test")
        assert widget._available_tags == tags

    def test_with_initial_value(self) -> None:
        """Initial value is stored."""
        widget = TagInput(value="work,urgent", id="test")
        assert widget._initial_value == "work,urgent"

    def test_valid_empty_always_true(self) -> None:
        """valid_empty property is always True."""
        widget = TagInput(id="test")
        assert widget.valid_empty is True
