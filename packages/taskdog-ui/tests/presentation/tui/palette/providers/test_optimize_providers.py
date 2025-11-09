"""Tests for optimize command providers."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

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

    def test_get_options_returns_two_commands(self):
        """Test that get_options returns both optimize commands."""
        options = self.provider.get_options(self.mock_app)

        self.assertEqual(len(options), 2)

        # Verify option names
        option_names = [opt[0] for opt in options]
        self.assertIn("Optimize", option_names)
        self.assertIn("Optimize (force)", option_names)

    @parameterized.expand(
        [
            ("optimize_normal", "Optimize", False),
            ("optimize_force", "Optimize (force)", True),
        ]
    )
    def test_option_callback_calls_search_optimize(
        self, scenario, option_name, expected_force
    ):
        """Test that selecting an option calls search_optimize with correct force flag."""
        options = self.provider.get_options(self.mock_app)

        # Find the option by name
        option = next((opt for opt in options if opt[0] == option_name), None)
        self.assertIsNotNone(option)

        # Get callback and invoke it
        callback = option[1]
        callback()

        # Verify search_optimize was called with correct force_override
        self.mock_app.search_optimize.assert_called_once_with(expected_force)

    def test_options_have_descriptions(self):
        """Test that all options have help text."""
        options = self.provider.get_options(self.mock_app)

        for _option_name, _callback, description in options:
            self.assertIsNotNone(description)
            self.assertTrue(len(description) > 0)


if __name__ == "__main__":
    unittest.main()
