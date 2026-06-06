"""Presenter for building a GanttViewModel from shared tasks + a Gantt overlay.

The presenter joins the canonical ``TaskRowDto`` list (shared with the table)
with the Gantt overlay and applies presentation logic (formatting,
strikethrough) to create presentation-ready view models.
"""

from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog.view_models.status import TaskStatus
from taskdog_core.application.dto.gantt_overlay import GanttOverlay
from taskdog_core.application.dto.task_dto import TaskRowDto


class GanttPresenter:
    """Presenter for building a GanttViewModel.

    This class is responsible for:
    1. Extracting necessary fields from the shared task list
    2. Applying presentation logic (strikethrough, formatting)
    3. Joining task data with the Gantt overlay into ViewModels
    """

    def present(self, tasks: list[TaskRowDto], overlay: GanttOverlay) -> GanttViewModel:
        """Build a GanttViewModel from the shared task list and overlay.

        Args:
            tasks: Canonical task DTOs (shared with the table view)
            overlay: Gantt-specific overlay (dates, allocations, workload)

        Returns:
            GanttViewModel with TaskGanttRowViewModel rows
        """
        task_view_models = [self._map_task_to_view_model(task) for task in tasks]

        return GanttViewModel(
            start_date=overlay.date_range.start_date,
            end_date=overlay.date_range.end_date,
            tasks=task_view_models,
            task_daily_hours=overlay.task_daily_hours,
            daily_workload=overlay.daily_workload,
            holidays=overlay.holidays,
            total_estimated_duration=overlay.total_estimated_duration,
        )

    def _map_task_to_view_model(self, task: TaskRowDto) -> TaskGanttRowViewModel:
        """Convert a TaskRowDto to TaskGanttRowViewModel.

        Applies presentation logic:
        - Formats estimated duration as string

        Args:
            task: TaskRowDto from the shared task list

        Returns:
            TaskGanttRowViewModel with presentation-ready data
        """
        # Format estimated duration
        formatted_estimated_duration = self._format_estimated_duration(
            task.estimated_duration
        )

        return TaskGanttRowViewModel(
            id=task.id,
            name=task.name,
            formatted_estimated_duration=formatted_estimated_duration,
            status=TaskStatus(task.status.value),
            planned_start=task.planned_start.date() if task.planned_start else None,
            planned_end=task.planned_end.date() if task.planned_end else None,
            actual_start=task.actual_start.date() if task.actual_start else None,
            actual_end=task.actual_end.date() if task.actual_end else None,
            deadline=task.deadline.date() if task.deadline else None,
            is_finished=task.is_finished,
        )

    def _format_estimated_duration(self, estimated_duration: float | None) -> str:
        """Format estimated duration for display.

        Args:
            estimated_duration: Estimated duration in hours (can be None)

        Returns:
            Formatted string (e.g., "8.0", "-")
        """
        if estimated_duration is None:
            return "-"
        return f"{estimated_duration:.1f}"
