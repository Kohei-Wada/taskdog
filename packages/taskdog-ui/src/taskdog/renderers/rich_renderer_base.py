"""Base class for Rich-based task renderers."""

from taskdog.constants.colors import STATUS_STYLES
from taskdog_core.domain.entities.task import TaskStatus


class RichRendererBase:
    """Base class for renderers using Rich library.

    Provides common utility methods for Rich-based rendering,
    including status styling.
    """

    def _get_status_style(self, status: TaskStatus) -> str:
        """Get Rich style for a task status.

        Args:
            status: Task status

        Returns:
            Rich style string (e.g., "yellow", "blue", "green", "red")
        """
        return STATUS_STYLES.get(status.value, "white")
