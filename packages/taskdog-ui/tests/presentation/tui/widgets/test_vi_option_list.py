"""Tests for ViOptionList widget."""

import pytest
from textual.widgets.option_list import Option

from taskdog.tui.widgets.vi_option_list import ViOptionList


class TestViOptionList:
    """Test cases for ViOptionList widget."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.options = [
            Option("Option 1"),
            Option("Option 2"),
            Option("Option 3"),
            Option("Option 4"),
            Option("Option 5"),
        ]

    def test_has_vi_bindings(self):
        """Test that ViOptionList has Vi-style key bindings defined."""
        widget = ViOptionList()
        binding_keys = {b.key for b in widget.BINDINGS}

        assert "j" in binding_keys
        assert "k" in binding_keys
        assert "g" in binding_keys
        assert "G" in binding_keys

    @pytest.mark.parametrize(
        "initial_index,expected_index",
        [
            (0, 1),
            (2, 3),
            (3, 4),
        ],
        ids=["from_start", "from_middle", "from_second_last"],
    )
    def test_action_cursor_down(self, initial_index, expected_index):
        """Test cursor down action (j key) moves cursor correctly."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_cursor_down()

        assert widget.highlighted == expected_index

    def test_action_cursor_down_at_bottom(self):
        """Test cursor down at bottom does not move beyond last option."""
        widget = ViOptionList(*self.options)
        widget.highlighted = 4  # Last index

        widget.action_cursor_down()

        assert widget.highlighted == 4  # Should stay at last index

    def test_action_cursor_down_with_none_highlighted(self):
        """Test cursor down with None highlighted does nothing."""
        widget = ViOptionList(*self.options)
        widget.highlighted = None

        widget.action_cursor_down()

        assert widget.highlighted is None

    @pytest.mark.parametrize(
        "initial_index,expected_index",
        [
            (4, 3),
            (2, 1),
            (1, 0),
        ],
        ids=["from_end", "from_middle", "from_second"],
    )
    def test_action_cursor_up(self, initial_index, expected_index):
        """Test cursor up action (k key) moves cursor correctly."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_cursor_up()

        assert widget.highlighted == expected_index

    def test_action_cursor_up_at_top(self):
        """Test cursor up at top does not move beyond first option."""
        widget = ViOptionList(*self.options)
        widget.highlighted = 0  # First index

        widget.action_cursor_up()

        assert widget.highlighted == 0  # Should stay at first index

    def test_action_cursor_up_with_none_highlighted(self):
        """Test cursor up with None highlighted does nothing."""
        widget = ViOptionList(*self.options)
        widget.highlighted = None

        widget.action_cursor_up()

        assert widget.highlighted is None

    @pytest.mark.parametrize(
        "initial_index",
        [0, 2, 4],
        ids=["from_start", "from_middle", "from_end"],
    )
    def test_action_scroll_home(self, initial_index):
        """Test scroll home action (g key) jumps to top."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_scroll_home()

        assert widget.highlighted == 0

    @pytest.mark.parametrize(
        "initial_index",
        [0, 2, 4],
        ids=["from_start", "from_middle", "from_end"],
    )
    def test_action_scroll_end(self, initial_index):
        """Test scroll end action (G key) jumps to bottom."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_scroll_end()

        assert widget.highlighted == 4

    def test_action_scroll_end_with_single_option(self):
        """Test scroll end with single option."""
        widget = ViOptionList(Option("Only option"))
        widget.highlighted = 0

        widget.action_scroll_end()

        assert widget.highlighted == 0

    def test_action_scroll_home_with_empty_list(self):
        """Test scroll home with empty list does not crash."""
        widget = ViOptionList()

        # Should not crash with empty list
        widget.action_scroll_home()

        # Highlighted remains None with empty list (no valid option to select)
        assert widget.highlighted is None
