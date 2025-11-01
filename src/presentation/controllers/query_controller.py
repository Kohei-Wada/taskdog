"""Query controller for orchestrating read-only operations.

This controller provides a shared interface between CLI, TUI, and future API layers
for read-only operations, eliminating code duplication in query service instantiation
and filter construction.
"""

from datetime import date

from application.dto.gantt_output import GanttOutput
from application.dto.tag_statistics_output import TagStatisticsOutput
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

        filtered_tasks = self.query_service.get_filtered_tasks(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=reverse,
        )

        return TaskListOutput(
            tasks=filtered_tasks,
            total_count=total_count,
            filtered_count=len(filtered_tasks),
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

    def get_task_by_id(self, task_id: int) -> Task | None:
        """Get a single task by ID.

        Simple wrapper around repository lookup for consistency.
        Used by various commands that need single task retrieval.

        Args:
            task_id: Task ID

        Returns:
            Task entity or None if not found
        """
        return self.repository.get_by_id(task_id)
