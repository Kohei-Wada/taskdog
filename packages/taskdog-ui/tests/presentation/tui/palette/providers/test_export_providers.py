"""Tests for export command providers."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

from taskdog.tui.palette.providers.export_providers import ExportFormatProvider


class TestExportFormatProvider(unittest.TestCase):
    """Test cases for ExportFormatProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_app = Mock()
        self.mock_app.command_factory = Mock()
        self.mock_app.command_factory.execute = Mock()
        self.mock_screen = Mock()
        self.mock_screen.app = self.mock_app
        self.provider = ExportFormatProvider(screen=self.mock_screen, match_style=None)

    def test_get_options_returns_three_formats(self):
        """Test that get_options returns all 3 export formats."""
        options = self.provider.get_options(self.mock_app)

        self.assertEqual(len(options), 3)

        # Verify option names
        option_names = [opt[0] for opt in options]
        self.assertIn("JSON", option_names)
        self.assertIn("CSV", option_names)
        self.assertIn("Markdown", option_names)

    @parameterized.expand(
        [
            ("json_format", "JSON", "json"),
            ("csv_format", "CSV", "csv"),
            ("markdown_format", "Markdown", "markdown"),
        ]
    )
    def test_option_callback_calls_export_command(
        self, scenario, option_name, expected_format_key
    ):
        """Test that selecting a format calls export command with correct format_key."""
        options = self.provider.get_options(self.mock_app)

        # Find the option by name
        option = next((opt for opt in options if opt[0] == option_name), None)
        self.assertIsNotNone(option)

        # Get callback and invoke it
        callback = option[1]
        callback()

        # Verify command_factory.execute was called with correct parameters
        self.mock_app.command_factory.execute.assert_called_once_with(
            "export", format_key=expected_format_key
        )

    def test_formats_have_descriptions(self):
        """Test that all formats have help text."""
        options = self.provider.get_options(self.mock_app)

        for _option_name, _callback, description in options:
            self.assertIsNotNone(description)
            self.assertTrue(len(description) > 0)
            self.assertIn("Export", description)


if __name__ == "__main__":
    unittest.main()
