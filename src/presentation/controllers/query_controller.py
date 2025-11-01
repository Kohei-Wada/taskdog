"""Query controller for orchestrating read-only operations.

This controller provides a shared interface between CLI, TUI, and future API layers
for read-only operations, eliminating code duplication in query service instantiation
and filter construction.
"""

from datetime import date

from application.dto.gantt_output import GanttOutput
from application.dto.get_task_by_id_output import GetTaskByIdOutput
from application.dto.tag_statistics_output import TagStatisticsOutput
from application.dto.task_dto import TaskDetailDto
from application.dto.task_list_output import TaskListOutput
from application.queries.filters.task_filter import TaskFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository


class QueryController:
    """Controller for task query operations (read-only).

    This class orchestrates query services, handling instantiation and providing
    a consistent interface for read-only operations. Presentation layers (CLI/TUI/API)
    only need to call controller methods with simple parameters, without knowing about
    query services or filter construction.

    Attributes:
        repository: Task repository for data access
        query_service: Task query service for complex queries
    """

    def __init__(self, repository: TaskRepository):
        """Initialize the query controller.

        Args:
            repository: Task repository
        """
        self.repository = repository
        self.query_service: TaskQueryService = TaskQueryService(repository)  # type: ignore[no-untyped-call]

    def list_tasks(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> TaskListOutput:
        """Get filtered and sorted task list.

        Retrieves tasks with optional filtering and sorting, along with count metadata.
        Used by table, today, week commands and future API endpoints.

        Args:
            filter_obj: Optional filter to apply
            sort_by: Field to sort by (default: "id")
            reverse: Reverse sort order (default: False)

        Returns:
            TaskListOutput with filtered tasks and counts
        """
        all_tasks = self.repository.get_all()
        total_count = len(all_tasks)

        filtered_task_dtos = self.query_service.get_filtered_tasks_as_dtos(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=reverse,
        )

        return TaskListOutput(
            tasks=filtered_task_dtos,
            total_count=total_count,
            filtered_count=len(filtered_task_dtos),
        )

    def get_gantt_data(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
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

        Returns:
            GanttOutput with chart data and workload information
        """
        return self.query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=reverse,
            start_date=start_date,
            end_date=end_date,
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

        # Calculate total number of tasks with at least one tag
        all_tasks = self.repository.get_all()
        total_tagged_tasks = sum(1 for task in all_tasks if task.tags)

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

    def _task_to_detail_dto(self, task: Task) -> TaskDetailDto:
        """Convert Task entity to TaskDetailDto.

        Args:
            task: Task entity

        Returns:
            TaskDetailDto with all task data
        """
        # Tasks from repository must have an ID
        assert task.id is not None, "Task must have an ID"

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
