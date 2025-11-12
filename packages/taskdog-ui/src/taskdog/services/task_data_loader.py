"""Task data loading service for TUI."""

from dataclasses import dataclass
from datetime import date

from taskdog.infrastructure.api_client import TaskdogApiClient
from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.presenters.table_presenter import TablePresenter
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.services.holiday_checker import IHolidayChecker


@dataclass
class TaskData:
    """Container for loaded task data.

    Attributes:
        all_tasks: All tasks loaded from API (cached)
        filtered_tasks: Tasks after applying display filter
        task_list_output: Original TaskListOutput from API
        table_view_models: ViewModels for table display
        gantt_view_model: Full gantt view model (cached)
        filtered_gantt_view_model: Gantt view model after display filter
    """

    all_tasks: list[TaskRowDto]
    filtered_tasks: list[TaskRowDto]
    task_list_output: TaskListOutput
    table_view_models: list[TaskRowViewModel]
    gantt_view_model: GanttViewModel | None = None
    filtered_gantt_view_model: GanttViewModel | None = None


class TaskDataLoader:
    """Loads and transforms task data for TUI display.

    Handles API calls, filtering, and ViewModel transformations.
    Separates data loading logic from UI coordination.
    """

    def __init__(
        self,
        api_client: TaskdogApiClient,
        table_presenter: TablePresenter,
        gantt_presenter: GanttPresenter,
        holiday_checker: IHolidayChecker | None = None,
    ):
        """Initialize TaskDataLoader.

        Args:
            api_client: API client for fetching tasks
            table_presenter: Presenter for table ViewModels
            gantt_presenter: Presenter for gantt ViewModels
            holiday_checker: Optional holiday checker for gantt data
        """
        self.api_client = api_client
        self.table_presenter = table_presenter
        self.gantt_presenter = gantt_presenter
        self.holiday_checker = holiday_checker

    def load_tasks(
        self,
        task_filter: TaskFilter | None,
        sort_by: str,
        reverse: bool = False,
        hide_completed: bool = False,
        date_range: tuple[date, date] | None = None,
    ) -> TaskData:
        """Load tasks from API and create ViewModels.

        Args:
            task_filter: Filter for API query
            sort_by: Sort field name
            reverse: Sort direction (default: False for ascending)
            hide_completed: Whether to hide completed/canceled tasks
            date_range: Optional (start_date, end_date) for gantt data

        Returns:
            TaskData containing all loaded data and ViewModels
        """
        # Fetch tasks from API with optional gantt data in a single request
        include_gantt = date_range is not None
        gantt_start_date, gantt_end_date = date_range if date_range else (None, None)

        task_list_output = self.api_client.list_tasks(
            filter_obj=task_filter,
            sort_by=sort_by,
            reverse=reverse,
            include_gantt=include_gantt,
            gantt_start_date=gantt_start_date,
            gantt_end_date=gantt_end_date,
            holiday_checker=self.holiday_checker,
        )

        # Cache all tasks
        all_tasks = task_list_output.tasks

        # Apply display filter
        filtered_tasks = self.apply_display_filter(all_tasks, hide_completed)

        # Create table ViewModels
        filtered_output = TaskListOutput(
            tasks=filtered_tasks,
            total_count=task_list_output.total_count,
            filtered_count=len(filtered_tasks),
        )
        table_view_models = self.table_presenter.present(filtered_output)

        # Convert gantt data from response if present
        gantt_view_model = None
        filtered_gantt_view_model = None
        if task_list_output.gantt_data:
            gantt_view_model = self.gantt_presenter.present(task_list_output.gantt_data)
            filtered_gantt_view_model = self.filter_gantt_by_tasks(
                gantt_view_model, filtered_tasks
            )

        return TaskData(
            all_tasks=all_tasks,
            filtered_tasks=filtered_tasks,
            task_list_output=task_list_output,
            table_view_models=table_view_models,
            gantt_view_model=gantt_view_model,
            filtered_gantt_view_model=filtered_gantt_view_model,
        )

    def load_gantt_data(
        self,
        task_filter: TaskFilter | None,
        sort_by: str,
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GanttViewModel:
        """Load gantt data from API.

        Args:
            task_filter: Filter for API query
            sort_by: Sort field name
            reverse: Sort direction (default: False for ascending)
            start_date: Start date for gantt
            end_date: End date for gantt

        Returns:
            GanttViewModel from presenter
        """
        gantt_output = self.api_client.get_gantt_data(
            filter_obj=task_filter,
            sort_by=sort_by,
            reverse=reverse,
            start_date=start_date,
            end_date=end_date,
            holiday_checker=self.holiday_checker,
        )
        return self.gantt_presenter.present(gantt_output)

    def apply_display_filter(
        self, tasks: list[TaskRowDto], hide_completed: bool
    ) -> list[TaskRowDto]:
        """Apply display filter based on hide_completed setting.

        Args:
            tasks: List of all tasks
            hide_completed: Whether to hide completed/canceled tasks

        Returns:
            Filtered list of tasks
        """
        if not hide_completed:
            return tasks

        return [
            task
            for task in tasks
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELED)
        ]

    def filter_gantt_by_tasks(
        self, gantt_view_model: GanttViewModel, tasks: list[TaskRowDto]
    ) -> GanttViewModel:
        """Filter gantt view model to match displayed tasks.

        Args:
            gantt_view_model: Full gantt view model
            tasks: List of tasks to display

        Returns:
            Filtered GanttViewModel
        """
        filtered_task_ids = {t.id for t in tasks}
        filtered_gantt_tasks = [
            task for task in gantt_view_model.tasks if task.id in filtered_task_ids
        ]

        return GanttViewModel(
            tasks=filtered_gantt_tasks,
            task_daily_hours=gantt_view_model.task_daily_hours,
            daily_workload=gantt_view_model.daily_workload,
            start_date=gantt_view_model.start_date,
            end_date=gantt_view_model.end_date,
            holidays=gantt_view_model.holidays,
        )
