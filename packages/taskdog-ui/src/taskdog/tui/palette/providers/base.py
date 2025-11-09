"""Base provider for list-based command palettes."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


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
