"""Tests for optimize command providers."""

from unittest.mock import Mock

import pytest

from taskdog.tui.palette.providers.optimize_providers import OptimizeCommandProvider


class TestOptimizeCommandProvider:
    """Test cases for OptimizeCommandProvider."""

    @pytest.fixture(autouse=True)
    def setup(self):
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

        assert len(options) == 1

        # Verify option name
        option_names = [opt[0] for opt in options]
        assert "Optimize" in option_names

    def test_option_callback_calls_search_optimize(self):
        """Test that selecting the option calls search_optimize."""
        options = self.provider.get_options(self.mock_app)

        # Find the Optimize option
        option = next((opt for opt in options if opt[0] == "Optimize"), None)
        assert option is not None

        # Get callback and invoke it
        callback = option[1]
        callback()

        # Verify search_optimize was called (no args, force is now in dialog)
        self.mock_app.search_optimize.assert_called_once_with()

    def test_options_have_descriptions(self):
        """Test that all options have help text."""
        options = self.provider.get_options(self.mock_app)

        for _option_name, _callback, description in options:
            assert description is not None
            assert len(description) > 0
