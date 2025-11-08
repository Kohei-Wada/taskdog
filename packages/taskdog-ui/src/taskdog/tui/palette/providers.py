"""Command providers for Taskdog TUI Command Palette."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, ClassVar, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


# Command metadata: (command_name, help_text, force_override)
OPTIMIZE_COMMANDS: list[tuple[str, str, bool]] = [
    ("Optimize", "Optimize schedule with selected algorithm", False),
    ("Optimize (force)", "Force optimize schedule (override existing)", True),
]

# Export format options: (format_key, format_name, description)
EXPORT_FORMATS: list[tuple[str, str, str]] = [
    ("json", "JSON", "Export tasks as JSON format"),
    ("csv", "CSV", "Export tasks as CSV format"),
    ("markdown", "Markdown", "Export tasks as Markdown table"),
]


class BaseListProvider(Provider):
    """Base provider for list-based command palettes.

    Eliminates code duplication by providing generic discover() and search()
    implementations. Subclasses only need to implement get_options().
    """

    @abstractmethod
    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return list of options for this provider.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of tuples: (option_name, callback, description)
        """
        ...

    async def discover(self) -> Hits:
        """Return all available options.

        Yields:
            DiscoveryHit objects for all options
        """
        app = cast("TaskdogTUI", self.app)
        for option_name, callback, description in self.get_options(app):
            yield DiscoveryHit(option_name, callback, help=description)

    async def search(self, query: str) -> Hits:
        """Search for options matching the query.

        Args:
            query: User's search query

        Yields:
            Hit objects for matching options
        """
        matcher = self.matcher(query)
        app = cast("TaskdogTUI", self.app)

        for option_name, callback, description in self.get_options(app):
            score = matcher.match(option_name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(option_name),
                    callback,
                    help=description,
                )


class SortCommandProvider(Provider):
    """Command provider for the main 'Sort' command."""

    async def discover(self) -> Hits:
        """Return the main Sort command.

        Yields:
            DiscoveryHit for the Sort command
        """
        app = cast("TaskdogTUI", self.app)
        yield DiscoveryHit(
            "Sort",
            app.search_sort,
            help="Change sort order for tasks and Gantt chart",
        )

    async def search(self, query: str) -> Hits:
        """Search for the Sort command.

        Args:
            query: User's search query

        Yields:
            Hit object if query matches "Sort"
        """
        matcher = self.matcher(query)
        app = cast("TaskdogTUI", self.app)

        command_name = "Sort"
        score = matcher.match(command_name)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command_name),
                app.search_sort,
                help="Change sort order for tasks and Gantt chart",
            )


class SortOptionsProvider(BaseListProvider):
    """Command provider for sort options (second stage)."""

    # Sort options: (sort_key, option_name, description)
    SORT_OPTIONS: ClassVar = [
        ("deadline", "Deadline", "Urgency-based (earlier deadline first)"),
        ("planned_start", "Planned Start", "Timeline-based (chronological order)"),
        ("priority", "Priority", "Importance-based (higher priority first)"),
        ("estimated_duration", "Duration", "Effort-based (shorter tasks first)"),
        ("id", "ID", "Creation order (lower ID first)"),
        ("name", "Name", "Alphabetically (A-Z)"),
    ]

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return sort options with callbacks.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (option_name, callback, description) tuples
        """
        return [
            (option_name, partial(app.set_sort_order, sort_key), description)
            for sort_key, option_name, description in self.SORT_OPTIONS
        ]


class OptimizeCommandProvider(BaseListProvider):
    """Command provider for optimization commands."""

    def get_options(self, app: TaskdogTUI) -> list[tuple[str, Callable[[], None], str]]:
        """Return optimize command options with callbacks.

        Args:
            app: TaskdogTUI application instance

        Returns:
            List of (command_name, callback, help_text) tuples
        """
        return [
            (command_name, partial(app.search_optimize, force_override), help_text)
            for command_name, help_text, force_override in OPTIMIZE_COMMANDS
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
            (format_name, partial(app.execute_export, format_key), description)
            for format_key, format_name, description in EXPORT_FORMATS
        ]
