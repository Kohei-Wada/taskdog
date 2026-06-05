"""Query controller for orchestrating read-only operations.

This controller provides a shared interface between CLI, TUI, and future API layers
for read-only operations, eliminating code duplication in query service instantiation
and filter construction.
"""

from datetime import date
from typing import TYPE_CHECKING

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)
from taskdog_core.application.use_cases.get_task_detail import GetTaskDetailUseCase
from taskdog_core.application.use_cases.list_tasks import ListTasksUseCase
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.time_provider import ITimeProvider

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class QueryController:
    """Controller for task query operations (read-only).

    This class orchestrates query services, handling instantiation and providing
    a consistent interface for read-only operations. Presentation layers (CLI/TUI/API)
    only need to call controller methods with simple parameters, without knowing about
    query services or filter construction.

    Attributes:
        repository: Task repository for data access
        notes_repository: Notes repository for task notes (optional)
        query_service: Task query service for complex queries
    """

    def __init__(
        self,
        repository: TaskRepository,
        notes_repository: NotesRepository | None,
        time_provider: ITimeProvider,
    ):
        """Initialize the query controller.

        Args:
            repository: Task repository
            notes_repository: Notes repository (optional, required for get_task_detail)
            time_provider: Provider for current time, supplied by the caller
        """
        self.repository = repository
        self.notes_repository = notes_repository
        self.query_service: TaskQueryService = TaskQueryService(
            repository, time_provider
        )

    def list_tasks(
        self,
        input_dto: ListTasksInput,
        include_gantt: bool = False,
        gantt_start_date: date | None = None,
        gantt_end_date: date | None = None,
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> TaskListOutput:
        """Get filtered and sorted task list using Input DTO.

        This method uses the ListTasksUseCase pattern, where filter construction
        is handled in the Application layer instead of the Presentation layer.

        Args:
            input_dto: Query parameters (filters, sorting) as Input DTO
            include_gantt: If True, include Gantt chart data in the output (default: False)
            gantt_start_date: Start date for Gantt chart (used when include_gantt=True)
            gantt_end_date: End date for Gantt chart (used when include_gantt=True)
            holiday_checker: Holiday checker for Gantt chart (used when include_gantt=True)

        Returns:
            TaskListOutput with filtered tasks, counts, and optionally the
            Gantt overlay (built from the same single fetch)
        """
        input_dto.include_gantt = include_gantt
        if include_gantt:
            input_dto.chart_start_date = gantt_start_date
            input_dto.chart_end_date = gantt_end_date

        use_case = ListTasksUseCase(
            repository=self.repository,
            query_service=self.query_service,
            holiday_checker=holiday_checker,
        )
        result = use_case.execute(input_dto)

        # Populate note existence info if notes_repository is available
        if self.notes_repository is not None and result.tasks:
            task_ids = [task.id for task in result.tasks]
            result.task_ids_with_notes = self.notes_repository.get_task_ids_with_notes(
                task_ids
            )

        return result

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics across all tasks.

        Calculates tag usage statistics including counts and metadata.
        Used by tags command (list mode) and future API endpoints.

        Returns:
            TagStatisticsOutput with tag counts and metadata
        """
        tag_counts = self.query_service.get_all_tags()
        total_tags = len(tag_counts)

        # Use SQL COUNT for efficiency instead of loading all tasks
        total_tagged_tasks = self.repository.count_tasks_with_tags()

        return TagStatisticsOutput(
            tag_counts=tag_counts,
            total_tags=total_tags,
            total_tagged_tasks=total_tagged_tasks,
        )

    def get_task_by_id(self, task_id: int) -> TaskByIdOutput:
        """Get a single task by ID.

        Retrieves a task and converts it to DTO.
        Used by TUI commands and other components that need single task retrieval.

        Args:
            task_id: Task ID

        Returns:
            TaskByIdOutput with TaskDetailDto (task=None if not found)
        """
        task = self.repository.get_by_id(task_id)
        if task is None:
            return TaskByIdOutput(task=None)

        # Convert Task to TaskDetailDto
        task_dto = TaskDetailDto.from_entity(task)
        return TaskByIdOutput(task=task_dto)

    def get_task_detail(self, task_id: int) -> TaskDetailOutput:
        """Get task details with notes.

        Retrieves a task along with its markdown notes file.
        Used by show command (CLI) and show_details_command (TUI).

        Args:
            task_id: Task ID

        Returns:
            TaskDetailOutput with task, notes_content, and has_notes

        Raises:
            ValueError: If notes_repository was not provided during initialization
            TaskNotFoundException: If task with given ID doesn't exist
        """
        if self.notes_repository is None:
            raise ValueError(
                "notes_repository is required for get_task_detail. "
                "Pass NotesRepository to QueryController.__init__"
            )

        use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)
        return use_case.execute(SingleTaskInput(task_id=task_id))

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get metadata for all available optimization algorithms.

        Returns:
            List of tuples (algorithm_id, display_name, description)
            for all registered optimization algorithms.

        Example:
            >>> metadata = query_controller.get_algorithm_metadata()
            >>> metadata[0]
            ('greedy', 'Greedy', 'Front-loads tasks (default)')
        """
        return StrategyFactory.get_algorithm_metadata()
