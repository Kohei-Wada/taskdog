"""Command providers for export functionality."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


# Export format options: (format_key, format_name, description)
EXPORT_FORMATS: list[tuple[str, str, str]] = [
    ("json", "JSON", "Export tasks as JSON format"),
    ("csv", "CSV", "Export tasks as CSV format"),
    ("markdown", "Markdown", "Export tasks as Markdown table"),
]


class ExportCommandProvider(Provider):
    """Command provider for the main 'Export' command."""

    async def discover(self) -> Hits:
        """Return the main Export command.

        Yields:
            DiscoveryHit for the Export command
        """
        app = cast("TaskdogTUI", self.app)
        yield DiscoveryHit(
            "Export",
            app.search_export,
            help="Export all tasks to file",
        )

    async def search(self, query: str) -> Hits:
        """Search for the Export command.

        Args:
            query: User's search query

        Yields:
            Hit object if query matches "Export"
        """
        matcher = self.matcher(query)
        app = cast("TaskdogTUI", self.app)

        command_name = "Export"
        score = matcher.match(command_name)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command_name),
                app.search_export,
                help="Export all tasks to file",
            )


class ExportFormatProvider(BaseListProvider):
    """Command provider for export format options (second stage)."""

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return export format options with callbacks.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (format_name, callback, description) tuples
        """
        return [
            (
                format_name,
                partial(app.command_factory.execute, "export", format_key=format_key),
                description,
            )
            for format_key, format_name, description in EXPORT_FORMATS
        ]
