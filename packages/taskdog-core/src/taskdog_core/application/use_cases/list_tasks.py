"""Use case for listing tasks with filtering and sorting."""

from typing import TYPE_CHECKING

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.queries.task_filter_builder import TaskFilterBuilder
from taskdog_core.application.use_cases.base import UseCase

if TYPE_CHECKING:
    from taskdog_core.application.queries.task_query_service import TaskQueryService
    from taskdog_core.domain.repositories.task_repository import TaskRepository


class ListTasksUseCase(UseCase[ListTasksInput, TaskListOutput]):
    """Use case for listing tasks with filtering and sorting.

    This use case encapsulates the business logic for querying tasks,
    including filter construction, query execution, and result assembly.

    It follows the same pattern as write use cases (CreateTaskUseCase, etc.)
    but is optimized for read operations.
    """

    def __init__(
        self,
        repository: "TaskRepository",
        query_service: "TaskQueryService",
    ):
        """Initialize use case with dependencies.

        Args:
            repository: Task repository for counting total tasks
            query_service: Query service for filtering and sorting
        """
        self.repository = repository
        self.query_service = query_service

    def execute(self, input_dto: ListTasksInput) -> TaskListOutput:
        """Execute the list tasks query.

        Builds filters from the input DTO, executes the query via
        TaskQueryService, and assembles the result with metadata.

        Args:
            input_dto: Query parameters (filters, sorting)

        Returns:
            TaskListOutput with filtered tasks and count metadata
        """
        # Build filter from input DTO
        filter_obj = TaskFilterBuilder.build(input_dto)

        # Get total count (before filtering)
        total_count = self.repository.count_tasks()

        # Execute filtered query
        task_dtos = self.query_service.get_filtered_tasks_as_dtos(
            filter_obj=filter_obj,
            sort_by=input_dto.sort_by,
            reverse=input_dto.reverse,
        )

        # Return result with metadata
        return TaskListOutput(
            tasks=task_dtos,
            total_count=total_count,
            filtered_count=len(task_dtos),
        )
