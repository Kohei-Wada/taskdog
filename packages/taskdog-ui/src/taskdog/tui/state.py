"""TUI application state management.

This module provides centralized state management for the TUI application.
All UI state is consolidated in the AppState class to provide a single source
of truth and enable easier debugging and testing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus

if TYPE_CHECKING:
    from taskdog.presenters.table_presenter import TablePresenter
    from taskdog.services.task_data_loader import TaskDataLoader


@dataclass
class AppState:
    """Central state manager for TUI application.

    This class consolidates all UI state that was previously scattered across
    the App and Widget classes. It provides a single source of truth for:
    - Display filters (hide_completed)
    - Sort order (gantt_sort_by)
    - Cached data (all_tasks, gantt_view_model)
    - ViewModels cache (for performance optimization)

    Attributes:
        hide_completed: Whether to hide completed/canceled tasks.
        gantt_sort_by: Sort field for gantt chart ("deadline", "priority", etc.).
        all_tasks: Cached list of all tasks from API.
        gantt_view_model: Cached gantt view model.
        cached_viewmodels: Cache of TaskRowViewModels to avoid re-presentation.
    """

    # Display filters
    hide_completed: bool = False
    gantt_sort_by: str = "deadline"
    search_query: str = ""  # Search query for filtering tasks

    # Cached data (DTOs from API)
    all_tasks: list[TaskRowDto] = field(default_factory=list)
    gantt_view_model: GanttViewModel | None = None

    # Derived ViewModels (computed from all_tasks + filters)
    table_viewmodels: list[TaskRowViewModel] = field(default_factory=list)
    filtered_gantt_viewmodel: GanttViewModel | None = None

    # ViewModels cache (for performance - avoid N+1 on toggle)
    cached_viewmodels: dict[int, TaskRowViewModel] = field(default_factory=dict)

    # Event notification callback (set by TUI app for reactive updates)
    _on_state_change: Callable[[str], None] | None = field(default=None, repr=False)

    def set_change_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback to be called when state changes.

        This is used by the TUI app to post UIUpdateRequested messages when state changes.

        Args:
            callback: Function to call with action name when state changes.
        """
        self._on_state_change = callback

    def _notify_change(self, action: str) -> None:
        """Notify that state has changed.

        Args:
            action: Description of what changed (e.g., "toggle_completed").
        """
        if self._on_state_change:
            self._on_state_change(action)

    def toggle_completed(self) -> None:
        """Toggle the hide_completed filter.

        This method flips the hide_completed flag, which controls whether
        completed and canceled tasks are shown in the UI.
        """
        self.hide_completed = not self.hide_completed
        self._notify_change("toggle_completed")

    def set_sort_by(self, sort_by: str) -> None:
        """Set the sort order for gantt chart.

        Args:
            sort_by: Sort field ("deadline", "priority", "planned_start", etc.).
        """
        self.gantt_sort_by = sort_by
        self._notify_change("set_sort_by")

    def get_filtered_tasks(self) -> list[TaskRowDto]:
        """Get filtered task list based on current state.

        This method applies the hide_completed filter to the cached all_tasks.
        Archived tasks are always filtered out.

        Returns:
            Filtered list of TaskRowDto objects.
        """
        filtered = []

        for task in self.all_tasks:
            # Always exclude archived tasks
            if task.is_archived:
                continue

            # Apply hide_completed filter
            if self.hide_completed and task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.CANCELED,
            ]:
                continue

            filtered.append(task)

        return filtered

    def clear_cached_viewmodels(self) -> None:
        """Clear the ViewModels cache.

        This should be called when tasks are modified (created, updated, deleted)
        to ensure the cache doesn't contain stale data.
        """
        self.cached_viewmodels.clear()

    def update_tasks_cache(self, tasks: list[TaskRowDto]) -> None:
        """Update the cached tasks list.

        Args:
            tasks: New list of tasks from API.
        """
        self.all_tasks = tasks
        self._notify_change("update_tasks_cache")

    def update_gantt_cache(self, gantt_view_model: GanttViewModel) -> None:
        """Update the cached gantt view model.

        Args:
            gantt_view_model: New gantt view model from API.
        """
        self.gantt_view_model = gantt_view_model
        self._notify_change("update_gantt_cache")

    def cache_viewmodel(self, task_id: int, viewmodel: TaskRowViewModel) -> None:
        """Cache a TaskRowViewModel.

        Args:
            task_id: Task ID.
            viewmodel: TaskRowViewModel to cache.
        """
        self.cached_viewmodels[task_id] = viewmodel

    def get_cached_viewmodel(self, task_id: int) -> TaskRowViewModel | None:
        """Get a cached TaskRowViewModel.

        Args:
            task_id: Task ID.

        Returns:
            Cached TaskRowViewModel, or None if not found.
        """
        return self.cached_viewmodels.get(task_id)

    def set_search_query(self, query: str) -> None:
        """Set the search query for filtering tasks.

        Args:
            query: Search query string.
        """
        self.search_query = query
        self._notify_change("set_search_query")

    def compute_table_viewmodels(self, presenter: TablePresenter) -> None:
        """Compute table ViewModels from current state.

        This method applies all current filters (hide_completed, search_query)
        to the cached tasks and generates ViewModels for table display.

        Args:
            presenter: TablePresenter for converting DTOs to ViewModels.
        """
        filtered_tasks = self.get_filtered_tasks()

        # Create TaskListOutput with filtered tasks
        output = TaskListOutput(
            tasks=filtered_tasks,
            total_count=len(self.all_tasks),
            filtered_count=len(filtered_tasks),
        )

        # Generate ViewModels
        self.table_viewmodels = presenter.present(output)

    def compute_filtered_gantt(self, loader: TaskDataLoader) -> None:
        """Compute filtered gantt ViewModel from current state.

        This method filters the gantt view model based on current filters
        (hide_completed, search_query).

        Args:
            loader: TaskDataLoader for filtering gantt data.
        """
        if not self.gantt_view_model:
            self.filtered_gantt_viewmodel = None
            return

        filtered_tasks = self.get_filtered_tasks()

        # Filter gantt view model by current filtered tasks
        self.filtered_gantt_viewmodel = loader.filter_gantt_by_tasks(
            self.gantt_view_model, filtered_tasks
        )
