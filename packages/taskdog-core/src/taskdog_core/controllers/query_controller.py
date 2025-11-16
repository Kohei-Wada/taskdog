"""Query controller for orchestrating read-only operations.

This controller provides a shared interface between CLI, TUI, and future API layers
for read-only operations, eliminating code duplication in query service instantiation
and filter construction.
"""

from datetime import date
from typing import TYPE_CHECKING

from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import GetTaskByIdOutput
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import GetTaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)
from taskdog_core.application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository

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
        notes_repository: NotesRepository | None = None,
    ):
        """Initialize the query controller.

        Args:
            repository: Task repository
            notes_repository: Notes repository (optional, required for get_task_detail)
        """
        self.repository = repository
        self.notes_repository = notes_repository
        self.query_service: TaskQueryService = TaskQueryService(repository)

    def list_tasks(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
        include_gantt: bool = False,
        gantt_start_date: date | None = None,
        gantt_end_date: date | None = None,
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> TaskListOutput:
        """Get filtered and sorted task list.

        Retrieves tasks with optional filtering and sorting, along with count metadata.
        Used by table, today, week commands and future API endpoints.

        Args:
            filter_obj: Optional filter to apply
            sort_by: Field to sort by (default: "id")
            reverse: Reverse sort order (default: False)
            include_gantt: If True, include Gantt chart data in the output (default: False)
            gantt_start_date: Start date for Gantt chart (used when include_gantt=True)
            gantt_end_date: End date for Gantt chart (used when include_gantt=True)
            holiday_checker: Holiday checker for Gantt chart (used when include_gantt=True)

        Returns:
            TaskListOutput with filtered tasks, counts, and optionally Gantt data
        """
        # Use SQL COUNT for efficiency instead of loading all tasks
        total_count = self.repository.count_tasks()

        filtered_task_dtos = self.query_service.get_filtered_tasks_as_dtos(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=reverse,
        )

        # Optionally include Gantt chart data
        gantt_data = None
        if include_gantt:
            gantt_data = self.get_gantt_data(
                filter_obj=filter_obj,
                sort_by=sort_by,
                reverse=reverse,
                start_date=gantt_start_date,
                end_date=gantt_end_date,
                holiday_checker=holiday_checker,
            )

        return TaskListOutput(
            tasks=filtered_task_dtos,
            total_count=total_count,
            filtered_count=len(filtered_task_dtos),
            gantt_data=gantt_data,
        )

    def get_gantt_data(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> GanttOutput:
        """Get Gantt chart data.

        Retrieves tasks formatted for Gantt chart display with workload calculations.
        Used by gantt command, TUI gantt view, and future API endpoints.

        Args:
            filter_obj: Optional filter to apply
            sort_by: Field to sort by (default: "deadline")
            reverse: Reverse sort order (default: False)
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            holiday_checker: Optional holiday checker for rendering holidays

        Returns:
            GanttOutput with chart data and workload information
        """
        return self.query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=reverse,
            start_date=start_date,
            end_date=end_date,
            holiday_checker=holiday_checker,
        )

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

    def get_task_by_id(self, task_id: int) -> GetTaskByIdOutput:
        """Get a single task by ID.

        Retrieves a task and converts it to DTO.
        Used by TUI commands and other components that need single task retrieval.

        Args:
            task_id: Task ID

        Returns:
            GetTaskByIdOutput with TaskDetailDto (task=None if not found)
        """
        task = self.repository.get_by_id(task_id)
        if task is None:
            return GetTaskByIdOutput(task=None)

        # Convert Task to TaskDetailDto
        task_dto = self._task_to_detail_dto(task)
        return GetTaskByIdOutput(task=task_dto)

    def get_task_detail(self, task_id: int) -> GetTaskDetailOutput:
        """Get task details with notes.

        Retrieves a task along with its markdown notes file.
        Used by show command (CLI) and show_details_command (TUI).

        Args:
            task_id: Task ID

        Returns:
            GetTaskDetailOutput with task, notes_content, and has_notes

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
        return use_case.execute(GetTaskDetailInput(task_id))

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

    def _task_to_detail_dto(self, task: Task) -> TaskDetailDto:
        """Convert Task entity to TaskDetailDto.

        Args:
            task: Task entity

        Returns:
            TaskDetailDto with all task data
        """
        # Tasks from repository must have an ID
        if task.id is None:
            raise ValueError("Task must have an ID")

        return TaskDetailDto(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            deadline=task.deadline,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            estimated_duration=task.estimated_duration,
            daily_allocations=task.daily_allocations,
            is_fixed=task.is_fixed,
            depends_on=task.depends_on,
            actual_daily_hours=task.actual_daily_hours,
            tags=task.tags,
            is_archived=task.is_archived,
            created_at=task.created_at,
            updated_at=task.updated_at,
            actual_duration_hours=task.actual_duration_hours,
            is_active=task.is_active,
            is_finished=task.is_finished,
            can_be_modified=task.can_be_modified,
            is_schedulable=task.is_schedulable(force_override=False),
        )
