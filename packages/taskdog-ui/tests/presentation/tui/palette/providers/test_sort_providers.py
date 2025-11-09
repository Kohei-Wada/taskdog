"""Tests for sort command providers."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

from taskdog.tui.palette.providers.sort_providers import SortOptionsProvider


class TestSortOptionsProvider(unittest.TestCase):
    """Test cases for SortOptionsProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = Mock()
        self.mock_app.set_sort_order = Mock()
        self.mock_screen = Mock()
        self.mock_screen.app = self.mock_app
        self.provider = SortOptionsProvider(screen=self.mock_screen, match_style=None)

    def test_get_options_returns_all_sort_options(self):
        """Test that get_options returns all 7 sort options."""
        options = self.provider.get_options(self.mock_app)

        self.assertEqual(len(options), 7)

        # Verify option names
        option_names = [opt[0] for opt in options]
        self.assertIn("Deadline", option_names)
        self.assertIn("Planned Start", option_names)
        self.assertIn("Priority", option_names)
        self.assertIn("Duration", option_names)
        self.assertIn("ID", option_names)
        self.assertIn("Name", option_names)
        self.assertIn("Status", option_names)

    @parameterized.expand(
        [
            ("deadline", "Deadline"),
            ("planned_start", "Planned Start"),
            ("priority", "Priority"),
            ("estimated_duration", "Duration"),
            ("id", "ID"),
            ("name", "Name"),
            ("status", "Status"),
        ]
    )
    def test_option_callback_calls_set_sort_order(self, sort_key, option_name):
        """Test that selecting an option calls set_sort_order with correct key."""
        options = self.provider.get_options(self.mock_app)

        # Find the option by name
        option = next((opt for opt in options if opt[0] == option_name), None)
        self.assertIsNotNone(option)

        # Get callback and invoke it
        callback = option[1]
        callback()

        # Verify set_sort_order was called with correct sort_key
        self.mock_app.set_sort_order.assert_called_once_with(sort_key)


if __name__ == "__main__":
    unittest.main()
