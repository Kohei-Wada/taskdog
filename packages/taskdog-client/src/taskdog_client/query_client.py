"""Task query operations client."""

from datetime import date
from typing import Any

from taskdog_client.base_client import BaseApiClient
from taskdog_client.converters import (
    convert_to_get_task_detail_output,
    convert_to_tag_statistics_output,
    convert_to_task_list_output,
)
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput


class QueryClient:
    """Client for task queries and data retrieval.

    Operations:
    - List tasks with filtering/sorting
    - Get individual tasks
    - Gantt chart data
    - Tag statistics
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize query client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

    def _build_list_params(
        self,
        include_archived: bool,
        sort_by: str,
        reverse: bool,
        status: str | None = None,
        tags: list[str] | None = None,
        **extra_params: Any,
    ) -> dict[str, Any]:
        """Build common parameters for list operations.

        Args:
            include_archived: Include archived tasks
            sort_by: Sort field
            reverse: Reverse sort order
            status: Filter by status
            tags: Filter by tags
            **extra_params: Additional parameters to include

        Returns:
            Dictionary of query parameters
        """
        params: dict[str, Any] = {
            "all": str(include_archived).lower(),
            "sort": sort_by,
            "reverse": str(reverse).lower(),
        }

        if status:
            params["status"] = status.lower()
        if tags:
            params["tags"] = tags

        # Add any extra parameters
        params.update(extra_params)

        return params

    def list_tasks(
        self,
        include_archived: bool = False,
        status: str | None = None,
        tags: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "id",
        reverse: bool = False,
        include_gantt: bool = False,
        gantt_start_date: date | None = None,
        gantt_end_date: date | None = None,
    ) -> TaskListOutput:
        """List tasks with optional filtering and sorting.

        Args:
            include_archived: Include archived tasks (default: False)
            status: Filter by status (e.g., "pending", "in_progress", "completed", "canceled")
            tags: Filter by tags (OR logic)
            start_date: Filter by start date
            end_date: Filter by end date
            sort_by: Sort field
            reverse: Reverse sort order
            include_gantt: If True, include Gantt chart data
            gantt_start_date: Gantt chart start date
            gantt_end_date: Gantt chart end date

        Returns:
            TaskListOutput with task list and metadata, optionally including Gantt data
        """
        # Build extra params for date filters and gantt options
        extra: dict[str, Any] = {"include_gantt": str(include_gantt).lower()}
        if start_date:
            extra["start_date"] = start_date.isoformat()
        if end_date:
            extra["end_date"] = end_date.isoformat()
        if include_gantt:
            if gantt_start_date:
                extra["gantt_start_date"] = gantt_start_date.isoformat()
            if gantt_end_date:
                extra["gantt_end_date"] = gantt_end_date.isoformat()

        params = self._build_list_params(
            include_archived, sort_by, reverse, status, tags, **extra
        )
        data = self._base._request_json("get", "/api/v1/tasks", params=params)
        return convert_to_task_list_output(data)

    def get_tasks_by_ids(self, task_ids: list[int]) -> TaskListOutput:
        """Get multiple tasks by their IDs in a single request.

        Batches what would otherwise be one get_task_by_id call per id into a
        single HTTP round trip. Missing ids are omitted; output order follows
        the input id order.

        Args:
            task_ids: Task IDs to retrieve

        Returns:
            TaskListOutput with the found tasks
        """
        if not task_ids:
            return TaskListOutput(tasks=[], total_count=0, filtered_count=0)

        data = self._base._request_json(
            "get", "/api/v1/tasks/by-ids", params={"ids": task_ids}
        )
        return convert_to_task_list_output(data)

    def get_task_by_id(self, task_id: int) -> TaskDetailOutput:
        """Get task by ID, including notes.

        Args:
            task_id: Task ID

        Returns:
            TaskDetailOutput with task data and notes

        Raises:
            TaskNotFoundException: If task not found
        """
        data = self._base._request_json("get", f"/api/v1/tasks/{task_id}")
        return convert_to_get_task_detail_output(data)

    def get_gantt_data(
        self,
        include_archived: bool = False,
        status: str | None = None,
        tags: list[str] | None = None,
        filter_start_date: date | None = None,
        filter_end_date: date | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TaskListOutput:
        """Get Gantt chart data.

        Returns the shared task list together with the Gantt overlay
        (``gantt_data``); callers join them by task id to build both the table
        and Gantt views.

        Args:
            include_archived: Include archived tasks (default: False)
            status: Filter by status
            tags: Filter by tags (OR logic)
            filter_start_date: Filter tasks by start date
            filter_end_date: Filter tasks by end date
            sort_by: Sort field
            reverse: Reverse sort order
            start_date: Chart display start date
            end_date: Chart display end date

        Returns:
            TaskListOutput with tasks and the Gantt overlay populated

        Note:
            filter_start_date/filter_end_date are for filtering tasks.
            start_date/end_date are for the chart display range.
        """
        # Build extra params for date filters and chart range
        extra: dict[str, Any] = {}
        if filter_start_date:
            extra["filter_start_date"] = filter_start_date.isoformat()
        if filter_end_date:
            extra["filter_end_date"] = filter_end_date.isoformat()
        if start_date:
            extra["start_date"] = start_date.isoformat()
        if end_date:
            extra["end_date"] = end_date.isoformat()

        params = self._build_list_params(
            include_archived, sort_by, reverse, status, tags, **extra
        )
        data = self._base._request_json("get", "/api/v1/gantt", params=params)
        return convert_to_task_list_output(data)

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics.

        Returns:
            TagStatisticsOutput with tag statistics
        """
        data = self._base._request_json("get", "/api/v1/tags/statistics")
        return convert_to_tag_statistics_output(data)
