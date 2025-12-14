"""Statistics command for TUI."""

from taskdog.mappers.statistics_mapper import StatisticsMapper
from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.screens.stats_screen import StatsScreen


class StatsCommand(TUICommandBase):
    """Command to show task statistics in a modal screen."""

    def execute_impl(self) -> None:
        """Execute the statistics command."""
        try:
            # Get statistics via API client
            result = self.context.api_client.calculate_statistics(period="all")

            # Convert to ViewModel
            view_model = StatisticsMapper.from_statistics_result(result)

            # Show statistics screen
            stats_screen = StatsScreen(view_model, period="all")
            self.app.push_screen(stats_screen)

        except Exception as e:
            self.notify_error("Failed to load statistics", e)
