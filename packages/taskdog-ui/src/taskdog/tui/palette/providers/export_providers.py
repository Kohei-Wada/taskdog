"""Command providers for export functionality."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from taskdog.tui.palette.providers.base import (
    BaseListProvider,
    SimpleSingleCommandProvider,
)

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


# Export format options: (format_key, format_name, description)
EXPORT_FORMATS: list[tuple[str, str, str]] = [
    ("json", "JSON", "Export tasks as JSON format"),
    ("csv", "CSV", "Export tasks as CSV format"),
    ("markdown", "Markdown", "Export tasks as Markdown table"),
]


class ExportCommandProvider(SimpleSingleCommandProvider):
    """Command provider for the main 'Export' command."""

    COMMAND_NAME = "Export"
    COMMAND_HELP = "Export all tasks to file"
    COMMAND_CALLBACK_NAME = "search_export"


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
