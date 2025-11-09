"""Tests for ViOptionList widget."""

import unittest

from parameterized import parameterized
from textual.widgets.option_list import Option

from taskdog.tui.widgets.vi_option_list import ViOptionList


class TestViOptionList(unittest.TestCase):
    """Test cases for ViOptionList widget."""

    def setUp(self):
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

        self.assertIn("j", binding_keys)
        self.assertIn("k", binding_keys)
        self.assertIn("g", binding_keys)
        self.assertIn("G", binding_keys)

    @parameterized.expand(
        [
            ("from_start", 0, 1),
            ("from_middle", 2, 3),
            ("from_second_last", 3, 4),
        ]
    )
    def test_action_cursor_down(self, _scenario, initial_index, expected_index):
        """Test cursor down action (j key) moves cursor correctly."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_cursor_down()

        self.assertEqual(widget.highlighted, expected_index)

    def test_action_cursor_down_at_bottom(self):
        """Test cursor down at bottom does not move beyond last option."""
        widget = ViOptionList(*self.options)
        widget.highlighted = 4  # Last index

        widget.action_cursor_down()

        self.assertEqual(widget.highlighted, 4)  # Should stay at last index

    def test_action_cursor_down_with_none_highlighted(self):
        """Test cursor down with None highlighted does nothing."""
        widget = ViOptionList(*self.options)
        widget.highlighted = None

        widget.action_cursor_down()

        self.assertIsNone(widget.highlighted)

    @parameterized.expand(
        [
            ("from_end", 4, 3),
            ("from_middle", 2, 1),
            ("from_second", 1, 0),
        ]
    )
    def test_action_cursor_up(self, _scenario, initial_index, expected_index):
        """Test cursor up action (k key) moves cursor correctly."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_cursor_up()

        self.assertEqual(widget.highlighted, expected_index)

    def test_action_cursor_up_at_top(self):
        """Test cursor up at top does not move beyond first option."""
        widget = ViOptionList(*self.options)
        widget.highlighted = 0  # First index

        widget.action_cursor_up()

        self.assertEqual(widget.highlighted, 0)  # Should stay at first index

    def test_action_cursor_up_with_none_highlighted(self):
        """Test cursor up with None highlighted does nothing."""
        widget = ViOptionList(*self.options)
        widget.highlighted = None

        widget.action_cursor_up()

        self.assertIsNone(widget.highlighted)

    @parameterized.expand(
        [
            ("from_start", 0),
            ("from_middle", 2),
            ("from_end", 4),
        ]
    )
    def test_action_scroll_home(self, _scenario, initial_index):
        """Test scroll home action (g key) jumps to top."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_scroll_home()

        self.assertEqual(widget.highlighted, 0)

    @parameterized.expand(
        [
            ("from_start", 0),
            ("from_middle", 2),
            ("from_end", 4),
        ]
    )
    def test_action_scroll_end(self, _scenario, initial_index):
        """Test scroll end action (G key) jumps to bottom."""
        widget = ViOptionList(*self.options)
        widget.highlighted = initial_index

        widget.action_scroll_end()

        self.assertEqual(widget.highlighted, 4)

    def test_action_scroll_end_with_single_option(self):
        """Test scroll end with single option."""
        widget = ViOptionList(Option("Only option"))
        widget.highlighted = 0

        widget.action_scroll_end()

        self.assertEqual(widget.highlighted, 0)

    def test_action_scroll_home_with_empty_list(self):
        """Test scroll home with empty list does not crash."""
        widget = ViOptionList()

        # Should not crash with empty list
        widget.action_scroll_home()

        # Highlighted remains None with empty list (no valid option to select)
        self.assertIsNone(widget.highlighted)


if __name__ == "__main__":
    unittest.main()
