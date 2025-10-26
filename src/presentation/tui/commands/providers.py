"""Command providers for Taskdog TUI Command Palette."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, ClassVar, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from presentation.tui.app import TaskdogTUI


# Command metadata: (command_name, help_text, force_override)
OPTIMIZE_COMMANDS: list[tuple[str, str, bool]] = [
    ("Optimize", "Optimize schedule with selected algorithm", False),
    ("Optimize (force)", "Force optimize schedule (override existing)", True),
]


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


class SortOptionsProvider(Provider):
    """Command provider for sort options (second stage)."""

    # Sort options: (sort_key, option_name, description)
    SORT_OPTIONS: ClassVar = [
        ("deadline", "Deadline", "Urgency-based (earlier deadline first)"),
        ("planned_start", "Planned Start", "Timeline-based (chronological order)"),
        ("priority", "Priority", "Importance-based (higher priority first)"),
        ("estimated_duration", "Duration", "Effort-based (shorter tasks first)"),
        ("id", "ID", "Creation order (lower ID first)"),
    ]

    async def discover(self) -> Hits:
        """Return all sort options.

        Yields:
            DiscoveryHit objects for all sort options
        """
        app = cast("TaskdogTUI", self.app)

        for sort_key, option_name, description in self.SORT_OPTIONS:
            yield DiscoveryHit(
                option_name,
                partial(app.set_sort_order, sort_key),
                help=description,
            )

    async def search(self, query: str) -> Hits:
        """Search for sort options.

        Args:
            query: User's search query

        Yields:
            Hit objects for matching sort options
        """
        matcher = self.matcher(query)
        app = cast("TaskdogTUI", self.app)

        for sort_key, option_name, description in self.SORT_OPTIONS:
            score = matcher.match(option_name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(option_name),
                    partial(app.set_sort_order, sort_key),
                    help=description,
                )


class OptimizeCommandProvider(Provider):
    """Command provider for optimization commands."""

    async def discover(self) -> Hits:
        """Return optimization commands.

        Yields:
            DiscoveryHit objects for Optimize and Force Optimize commands
        """
        app = cast("TaskdogTUI", self.app)

        for command_name, help_text, force_override in OPTIMIZE_COMMANDS:
            yield DiscoveryHit(
                command_name,
                partial(app.search_optimize, force_override),
                help=help_text,
            )

    async def search(self, query: str) -> Hits:
        """Search for optimization commands.

        Args:
            query: User's search query

        Yields:
            Hit objects for matching optimization commands
        """
        matcher = self.matcher(query)
        app = cast("TaskdogTUI", self.app)

        for command_name, help_text, force_override in OPTIMIZE_COMMANDS:
            score = matcher.match(command_name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(command_name),
                    partial(app.search_optimize, force_override),
                    help=help_text,
                )
