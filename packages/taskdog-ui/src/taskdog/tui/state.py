"""TUI application state management.

This module provides centralized state management for the TUI application.
All UI state is consolidated in the AppState class to provide a single source
of truth and enable easier debugging and testing.
"""

from dataclasses import dataclass, field

from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


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

    # Cached data (DTOs from API)
    all_tasks: list[TaskRowDto] = field(default_factory=list)
    gantt_view_model: GanttViewModel | None = None

    # ViewModels cache (for performance - avoid N+1 on toggle)
    cached_viewmodels: dict[int, TaskRowViewModel] = field(default_factory=dict)

    def toggle_completed(self) -> None:
        """Toggle the hide_completed filter.

        This method flips the hide_completed flag, which controls whether
        completed and canceled tasks are shown in the UI.
        """
        self.hide_completed = not self.hide_completed

    def set_sort_by(self, sort_by: str) -> None:
        """Set the sort order for gantt chart.

        Args:
            sort_by: Sort field ("deadline", "priority", "planned_start", etc.).
        """
        self.gantt_sort_by = sort_by

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

    def update_gantt_cache(self, gantt_view_model: GanttViewModel) -> None:
        """Update the cached gantt view model.

        Args:
            gantt_view_model: New gantt view model from API.
        """
        self.gantt_view_model = gantt_view_model

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
