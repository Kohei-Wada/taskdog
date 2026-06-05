"""Use case for listing tasks with filtering and sorting."""

from typing import TYPE_CHECKING

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.queries.task_filter_builder import TaskFilterBuilder
from taskdog_core.application.use_cases.base import UseCase

if TYPE_CHECKING:
    from taskdog_core.application.queries.task_query_service import TaskQueryService
    from taskdog_core.domain.repositories.task_repository import TaskRepository
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class ListTasksUseCase(UseCase[ListTasksInput, TaskListOutput]):
    """Use case for listing tasks with filtering and sorting.

    This use case encapsulates the business logic for querying tasks,
    including filter construction, query execution, and result assembly.

    When ``input_dto.include_gantt`` is set, it also builds the Gantt overlay
    from the same fetched task set, so the table and Gantt views share a single
    query instead of fetching the same filtered set twice.
    """

    def __init__(
        self,
        repository: "TaskRepository",
        query_service: "TaskQueryService",
        holiday_checker: "IHolidayChecker | None" = None,
    ):
        """Initialize use case with dependencies.

        Args:
            repository: Task repository for counting total tasks
            query_service: Query service for filtering and sorting
            holiday_checker: Optional holiday checker for the Gantt overlay
        """
        self.repository = repository
        self.query_service = query_service
        self.holiday_checker = holiday_checker

    def execute(self, input_dto: ListTasksInput) -> TaskListOutput:
        """Execute the list tasks query.

        Builds filters from the input DTO, fetches the filtered tasks once, and
        assembles the result. When ``include_gantt`` is set, the Gantt overlay
        is computed from the same task set.

        Args:
            input_dto: Query parameters (filters, sorting, optional Gantt range)

        Returns:
            TaskListOutput with filtered tasks, count metadata, and optionally
            the Gantt overlay
        """
        # Build filter from input DTO
        filter_obj = TaskFilterBuilder.build(input_dto)

        # Get total count (before filtering)
        total_count = self.repository.count_tasks()

        # Execute filtered query once (shared by table and Gantt overlay)
        tasks = self.query_service.get_filtered_tasks(
            filter_obj=filter_obj,
            sort_by=input_dto.sort_by,
            reverse=input_dto.reverse,
        )
        task_dtos = [TaskRowDto.from_entity(task) for task in tasks]

        result = TaskListOutput(
            tasks=task_dtos,
            total_count=total_count,
            filtered_count=len(task_dtos),
        )

        # Optionally build the Gantt overlay from the same fetched task set
        if input_dto.include_gantt:
            result.gantt_data = self.query_service.build_gantt_overlay(
                tasks=tasks,
                start_date=input_dto.chart_start_date,
                end_date=input_dto.chart_end_date,
                holiday_checker=self.holiday_checker,
            )

        return result
