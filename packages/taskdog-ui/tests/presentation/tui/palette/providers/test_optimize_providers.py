"""Tests for optimize command providers."""

import unittest
from unittest.mock import Mock

from taskdog.tui.palette.providers.optimize_providers import OptimizeCommandProvider


class TestOptimizeCommandProvider(unittest.TestCase):
    """Test cases for OptimizeCommandProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = Mock()
        self.mock_app.search_optimize = Mock()
        self.mock_screen = Mock()
        self.mock_screen.app = self.mock_app
        self.provider = OptimizeCommandProvider(
            screen=self.mock_screen, match_style=None
        )

    def test_get_options_returns_single_command(self):
        """Test that get_options returns single optimize command."""
        options = self.provider.get_options(self.mock_app)

        self.assertEqual(len(options), 1)

        # Verify option name
        option_names = [opt[0] for opt in options]
        self.assertIn("Optimize", option_names)

    def test_option_callback_calls_search_optimize(self):
        """Test that selecting the option calls search_optimize."""
        options = self.provider.get_options(self.mock_app)

        # Find the Optimize option
        option = next((opt for opt in options if opt[0] == "Optimize"), None)
        self.assertIsNotNone(option)

        # Get callback and invoke it
        callback = option[1]
        callback()

        # Verify search_optimize was called (no args, force is now in dialog)
        self.mock_app.search_optimize.assert_called_once_with()

    def test_options_have_descriptions(self):
        """Test that all options have help text."""
        options = self.provider.get_options(self.mock_app)

        for _option_name, _callback, description in options:
            self.assertIsNotNone(description)
            self.assertTrue(len(description) > 0)


if __name__ == "__main__":
    unittest.main()
