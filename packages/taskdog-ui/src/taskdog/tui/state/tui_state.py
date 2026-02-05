"""TUI application state management.

This module provides centralized state management for the TUI application,
eliminating duplication and synchronization issues across components.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto

if TYPE_CHECKING:
    from taskdog.tui.widgets.task_search_filter import TaskSearchFilter


@dataclass
class TUIState:
    """TUI application state container.

    Centralizes all shared state across TUI components to prevent
    duplication and synchronization issues.

    State Categories:
    - Sort Settings: sort_by, sort_reverse
    - Filter Settings: current_query, filter_chain, gantt_filter_enabled
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

    # === Filter Settings ===
    current_query: str = ""
    """Current search query string."""

    filter_chain: list[str] = field(default_factory=list)
    """Progressive filter chain for refined searches."""

    gantt_filter_enabled: bool = False
    """Whether to apply search filter to Gantt chart."""

    # === Data Caches ===
    tasks_cache: list[TaskRowDto] = field(default_factory=list)
    """Cache of all tasks (DTO format) from last API fetch."""

    viewmodels_cache: list[TaskRowViewModel] = field(default_factory=list)
    """Cache of table ViewModels (converted from tasks_cache)."""

    gantt_cache: GanttViewModel | None = None
    """Cache of Gantt ViewModel for current date range."""

    # === Internal State (not exposed) ===
    _search_filter: "TaskSearchFilter | None" = field(
        default=None, repr=False, compare=False
    )
    """Lazily initialized search filter instance."""

    def _get_search_filter(self) -> "TaskSearchFilter":
        """Get or create the search filter instance (lazy initialization).

        Returns:
            TaskSearchFilter instance
        """
        if self._search_filter is None:
            from taskdog.tui.widgets.task_search_filter import TaskSearchFilter

            self._search_filter = TaskSearchFilter()
        return self._search_filter

    # === Filter Methods ===
    def set_filter(self, query: str) -> None:
        """Set the current search query.

        Args:
            query: Search query string
        """
        self.current_query = query

    def add_to_filter_chain(self, query: str) -> None:
        """Add current query to filter chain for progressive filtering.

        Args:
            query: Filter query to add to the chain
        """
        if query:
            self.filter_chain.append(query)
            # Clear current query after adding to chain
            self.current_query = ""

    def clear_filters(self) -> None:
        """Clear all filters (current query and filter chain)."""
        self.current_query = ""
        self.filter_chain = []

    def toggle_gantt_filter(self) -> bool:
        """Toggle Gantt filter enabled/disabled.

        Returns:
            New state of gantt_filter_enabled
        """
        self.gantt_filter_enabled = not self.gantt_filter_enabled
        return self.gantt_filter_enabled

    # === Computed Properties ===
    @property
    def is_filtered(self) -> bool:
        """Check if any filter is currently active.

        Returns:
            True if there is a current query or filter chain
        """
        return bool(self.current_query or self.filter_chain)

    @property
    def filtered_task_ids(self) -> set[int]:
        """Get IDs of tasks that match the current filter.

        Returns:
            Set of task IDs matching the filter
        """
        return {vm.id for vm in self.filtered_viewmodels}

    @property
    def filtered_tasks(self) -> list[TaskRowDto]:
        """Get tasks for display.

        Returns:
            All tasks from cache.
        """
        return self.tasks_cache

    @property
    def filtered_viewmodels(self) -> list[TaskRowViewModel]:
        """Get ViewModels for display, with filter applied.

        Returns:
            Filtered ViewModels based on current query and filter chain.
        """
        search_filter = self._get_search_filter()
        filtered_vms = self.viewmodels_cache

        # Apply filter chain first
        for filter_query in self.filter_chain:
            filtered_vms = search_filter.filter(filtered_vms, filter_query)

        # Apply current query to the chain result
        if self.current_query:
            filtered_vms = search_filter.filter(filtered_vms, self.current_query)

        return filtered_vms

    @property
    def match_count(self) -> int:
        """Get the number of currently displayed (matched) tasks.

        Returns:
            Number of tasks matching current filter
        """
        return len(self.filtered_viewmodels)

    @property
    def total_count(self) -> int:
        """Get the total number of tasks (unfiltered).

        Returns:
            Total number of tasks in cache
        """
        return len(self.viewmodels_cache)

    @property
    def filtered_gantt(self) -> GanttViewModel | None:
        """Get Gantt ViewModel with filter applied if enabled.

        Returns:
            Filtered GanttViewModel if gantt_filter_enabled and filter active,
            otherwise returns the full gantt_cache.
        """
        if self.gantt_cache is None:
            return None

        # Return full data if gantt filter is disabled or no filter is active
        if not self.gantt_filter_enabled or not self.is_filtered:
            return self.gantt_cache

        # Filter tasks by matching IDs from filtered_viewmodels
        filtered_ids = self.filtered_task_ids
        filtered_tasks: list[TaskGanttRowViewModel] = [
            t for t in self.gantt_cache.tasks if t.id in filtered_ids
        ]
        filtered_daily_hours: dict[int, dict[date, float]] = {
            task_id: hours
            for task_id, hours in self.gantt_cache.task_daily_hours.items()
            if task_id in filtered_ids
        }

        # Use original daily_workload and total_estimated_duration from cache
        # These represent total scheduled work, independent of display filtering
        return GanttViewModel(
            start_date=self.gantt_cache.start_date,
            end_date=self.gantt_cache.end_date,
            tasks=filtered_tasks,
            task_daily_hours=filtered_daily_hours,
            daily_workload=self.gantt_cache.daily_workload,
            holidays=self.gantt_cache.holidays,
            total_estimated_duration=self.gantt_cache.total_estimated_duration,
        )

    def clear_caches(self) -> None:
        """Clear all cached data.

        Called when forcing a full refresh from the API.
        Resets all cache fields to their initial empty state.
        Note: Does not clear filter state - filters persist across refreshes.
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
