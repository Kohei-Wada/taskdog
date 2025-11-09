"""Command providers for sort functionality."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, ClassVar, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider

from taskdog.tui.palette.providers.base import BaseListProvider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


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
        (
            "status",
            "Status",
            "State-based (CANCELED → COMPLETED → IN_PROGRESS → PENDING)",
        ),
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
