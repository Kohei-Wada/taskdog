"""TUI application state management.

This module provides centralized state management for the TUI application,
eliminating duplication and synchronization issues across components.
"""

from dataclasses import dataclass, field

from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto


@dataclass
class TUIState:
    """TUI application state container.

    Centralizes all shared state across TUI components to prevent
    duplication and synchronization issues.

    State Categories:
    - Sort Settings: sort_by, sort_reverse
    - Data Caches: tasks_cache, viewmodels_cache, gantt_cache

    This class serves as the Single Source of Truth (SSoT) for all
    application state, replacing scattered state fields across
    TaskdogTUI, GanttWidget, and TaskTable.
    """

    # === Sort Settings ===
    sort_by: str = "deadline"
    """Sort field for Gantt and task list (deadline, priority, etc.)."""

    sort_reverse: bool = False
    """Sort direction: False=ascending, True=descending."""

    # === Data Caches ===
    tasks_cache: list[TaskRowDto] = field(default_factory=list)
    """Cache of all tasks (DTO format) from last API fetch."""

    viewmodels_cache: list[TaskRowViewModel] = field(default_factory=list)
    """Cache of table ViewModels (converted from tasks_cache)."""

    gantt_cache: GanttViewModel | None = None
    """Cache of Gantt ViewModel for current date range."""

    # === Computed Properties ===
    @property
    def filtered_tasks(self) -> list[TaskRowDto]:
        """Get tasks for display.

        Returns:
            All tasks from cache.
        """
        return self.tasks_cache

    @property
    def filtered_viewmodels(self) -> list[TaskRowViewModel]:
        """Get ViewModels for display.

        Returns:
            All ViewModels from cache.
        """
        return self.viewmodels_cache

    def clear_caches(self) -> None:
        """Clear all cached data.

        Called when forcing a full refresh from the API.
        Resets all cache fields to their initial empty state.
        """
        self.tasks_cache.clear()
        self.viewmodels_cache.clear()
        self.gantt_cache = None

    def update_caches(
        self,
        tasks: list[TaskRowDto],
        viewmodels: list[TaskRowViewModel],
        gantt: GanttViewModel | None = None,
    ) -> None:
        """Update all caches atomically.

        This method ensures that all caches are updated together
        to prevent inconsistencies between task data and viewmodels.

        Args:
            tasks: New task data from API (DTO format)
            viewmodels: New ViewModels for table display
            gantt: New Gantt ViewModel (optional, only updated if provided)

        Raises:
            ValueError: If tasks and viewmodels have different lengths
        """
        if len(tasks) != len(viewmodels):
            raise ValueError(
                f"tasks and viewmodels must have same length: {len(tasks)} != {len(viewmodels)}"
            )

        self.tasks_cache = tasks
        self.viewmodels_cache = viewmodels
        if gantt is not None:
            self.gantt_cache = gantt

    def invalidate_gantt_cache(self) -> None:
        """Invalidate only Gantt cache.

        Useful when Gantt needs to be recalculated (e.g., on resize)
        without reloading all task data.
        """
        self.gantt_cache = None
