"""Tests for optimize command providers."""

from taskdog.tui.palette.providers.base import SimpleSingleCommandProvider
from taskdog.tui.palette.providers.optimize_providers import OptimizeCommandProvider


class TestOptimizeCommandProvider:
    """Test cases for OptimizeCommandProvider."""

    def test_inherits_simple_single_command_provider(self):
        """Test that OptimizeCommandProvider uses SimpleSingleCommandProvider."""
        assert issubclass(OptimizeCommandProvider, SimpleSingleCommandProvider)

    def test_command_attributes(self):
        """Test that class attributes are correctly defined."""
        assert OptimizeCommandProvider.COMMAND_NAME == "Optimize"
        assert OptimizeCommandProvider.COMMAND_CALLBACK_NAME == "search_optimize"
        assert len(OptimizeCommandProvider.COMMAND_HELP) > 0
