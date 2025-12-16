"""Presenter for converting GanttOutput DTO to GanttViewModel.

This presenter extracts necessary fields from GanttTaskDto and applies
presentation logic (formatting, strikethrough) to create presentation-ready
view models.
"""

from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.task_dto import GanttTaskDto


class GanttPresenter:
    """Presenter for converting GanttOutput to GanttViewModel.

    This class is responsible for:
    1. Extracting necessary fields from Task entities
    2. Applying presentation logic (strikethrough, formatting)
    3. Converting domain data to presentation-ready ViewModels
    """

    def present(self, gantt_result: GanttOutput) -> GanttViewModel:
        """Convert GanttOutput DTO to GanttViewModel.

        Args:
            gantt_result: Application layer DTO with GanttTaskDto

        Returns:
            GanttViewModel with TaskGanttRowViewModel
        """
        # Convert each GanttTaskDto to TaskGanttRowViewModel
        task_view_models = [
            self._map_task_to_view_model(task) for task in gantt_result.tasks
        ]

        return GanttViewModel(
            start_date=gantt_result.date_range.start_date,
            end_date=gantt_result.date_range.end_date,
            tasks=task_view_models,
            task_daily_hours=gantt_result.task_daily_hours,
            daily_workload=gantt_result.daily_workload,
            holidays=gantt_result.holidays,
            total_estimated_duration=gantt_result.total_estimated_duration,
        )

    def _map_task_to_view_model(self, task: GanttTaskDto) -> TaskGanttRowViewModel:
        """Convert a GanttTaskDto to TaskGanttRowViewModel.

        Applies presentation logic:
        - Adds strikethrough to task name if finished
        - Formats estimated duration as string

        Args:
            task: GanttTaskDto from application layer

        Returns:
            TaskGanttRowViewModel with presentation-ready data
        """
        # Apply strikethrough for finished tasks
        formatted_name = task.name
        if task.is_finished:
            formatted_name = f"[strike]{task.name}[/strike]"

        # Format estimated duration
        formatted_estimated_duration = self._format_estimated_duration(
            task.estimated_duration
        )

        return TaskGanttRowViewModel(
            id=task.id,
            name=task.name,
            formatted_name=formatted_name,
            estimated_duration=task.estimated_duration,
            formatted_estimated_duration=formatted_estimated_duration,
            status=task.status,
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
