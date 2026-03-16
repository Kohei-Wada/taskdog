"""Task data loading service for TUI."""

from dataclasses import dataclass
from datetime import date

from taskdog_client import TaskdogApiClient

from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.presenters.table_presenter import TablePresenter
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput


@dataclass
class TaskData:
    """Container for loaded task data.

    Attributes:
        all_tasks: All tasks loaded from API (cached)
        task_list_output: Original TaskListOutput from API
        table_view_models: ViewModels for table display
        gantt_view_model: Full gantt view model (cached)
    """

    all_tasks: list[TaskRowDto]
    task_list_output: TaskListOutput
    table_view_models: list[TaskRowViewModel]
    gantt_view_model: GanttViewModel | None = None


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
    ):
        """Initialize TaskDataLoader.

        Args:
            api_client: API client for fetching tasks
            table_presenter: Presenter for table ViewModels
            gantt_presenter: Presenter for gantt ViewModels
        """
        self.api_client = api_client
        self.table_presenter = table_presenter
        self.gantt_presenter = gantt_presenter

    def load_tasks(
        self,
        include_archived: bool = False,
        sort_by: str = "id",
        reverse: bool = False,
        date_range: tuple[date, date] | None = None,
    ) -> TaskData:
        """Load tasks from API and create ViewModels.

        Args:
            include_archived: Include archived tasks (default: False)
            sort_by: Sort field name
            reverse: Sort direction (default: False for ascending)
            date_range: Optional (start_date, end_date) for gantt data

        Returns:
            TaskData containing all loaded data and ViewModels
        """
        # Fetch tasks from API with optional gantt data in a single request
        include_gantt = date_range is not None
        gantt_start_date, gantt_end_date = date_range or (None, None)

        task_list_output = self.api_client.list_tasks(
            include_archived=include_archived,
            sort_by=sort_by,
            reverse=reverse,
            include_gantt=include_gantt,
            gantt_start_date=gantt_start_date,
            gantt_end_date=gantt_end_date,
        )

        all_tasks = task_list_output.tasks

        # Create table ViewModels from all tasks
        # TUIState will handle search filtering via filtered_viewmodels property
        all_tasks_output = TaskListOutput(
            tasks=all_tasks,
            total_count=task_list_output.total_count,
            filtered_count=len(all_tasks),
        )
        table_view_models = self.table_presenter.present(all_tasks_output)

        # Convert gantt data from response if present
        gantt_view_model = None
        if task_list_output.gantt_data:
            gantt_view_model = self.gantt_presenter.present(task_list_output.gantt_data)

        return TaskData(
            all_tasks=all_tasks,
            task_list_output=task_list_output,
            table_view_models=table_view_models,
            gantt_view_model=gantt_view_model,
        )
