"""Task query operations client."""

from datetime import date
from typing import Any

from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog.infrastructure.api.converters import (
    convert_to_gantt_output,
    convert_to_get_task_by_id_output,
    convert_to_get_task_detail_output,
    convert_to_tag_statistics_output,
    convert_to_task_list_output,
)
from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
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

    def __init__(self, base_client: BaseApiClient, has_notes_cache: dict[int, bool]):
        """Initialize query client.

        Args:
            base_client: Base API client for HTTP operations
            has_notes_cache: Shared cache for has_notes information
        """
        self._base = base_client
        self._has_notes_cache = has_notes_cache

    def list_tasks(
        self,
        all: bool = False,
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
            all: Include archived tasks (default: False)
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
        params: dict[str, Any] = {
            "all": str(all).lower(),
            "sort": sort_by,
            "reverse": str(reverse).lower(),
            "include_gantt": str(include_gantt).lower(),
        }

        # Add filter parameters if provided
        if status:
            params["status"] = status.lower()
        if tags:
            params["tags"] = tags
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        if include_gantt:
            if gantt_start_date:
                params["gantt_start_date"] = gantt_start_date.isoformat()
            if gantt_end_date:
                params["gantt_end_date"] = gantt_end_date.isoformat()

        response = self._base._safe_request("get", "/api/v1/tasks", params=params)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_list_output(data, self._has_notes_cache)

    def list_today_tasks(
        self,
        all: bool = False,
        status: str | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
    ) -> TaskListOutput:
        """List tasks relevant for today.

        Includes tasks that:
        - Have deadline today
        - Have planned period including today
        - Are IN_PROGRESS (regardless of dates)

        Args:
            all: Include archived tasks (default: False)
            status: Filter by status
            sort_by: Sort field (default: deadline)
            reverse: Reverse sort order

        Returns:
            TaskListOutput with today's tasks
        """
        params: dict[str, Any] = {
            "all": str(all).lower(),
            "sort": sort_by,
            "reverse": str(reverse).lower(),
        }

        if status:
            params["status"] = status.lower()

        response = self._base._safe_request("get", "/api/v1/tasks/today", params=params)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_list_output(data, self._has_notes_cache)

    def list_week_tasks(
        self,
        all: bool = False,
        status: str | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
    ) -> TaskListOutput:
        """List tasks relevant for this week.

        Includes tasks that:
        - Have deadline within this week (Monday to Sunday)
        - Have planned period overlapping this week
        - Are IN_PROGRESS (regardless of dates)

        Args:
            all: Include archived tasks (default: False)
            status: Filter by status
            sort_by: Sort field (default: deadline)
            reverse: Reverse sort order

        Returns:
            TaskListOutput with this week's tasks
        """
        params: dict[str, Any] = {
            "all": str(all).lower(),
            "sort": sort_by,
            "reverse": str(reverse).lower(),
        }

        if status:
            params["status"] = status.lower()

        response = self._base._safe_request("get", "/api/v1/tasks/week", params=params)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_task_list_output(data, self._has_notes_cache)

    def get_task_by_id(self, task_id: int) -> TaskByIdOutput:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            TaskByIdOutput with task data

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("get", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_get_task_by_id_output(data)

    def get_task_detail(self, task_id: int) -> TaskDetailOutput:
        """Get task details with notes.

        Args:
            task_id: Task ID

        Returns:
            TaskDetailOutput with task data and notes

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._base._safe_request("get", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_get_task_detail_output(data)

    def get_gantt_data(
        self,
        all: bool = False,
        status: str | None = None,
        tags: list[str] | None = None,
        filter_start_date: date | None = None,
        filter_end_date: date | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GanttOutput:
        """Get Gantt chart data.

        Args:
            all: Include archived tasks (default: False)
            status: Filter by status
            tags: Filter by tags (OR logic)
            filter_start_date: Filter tasks by start date
            filter_end_date: Filter tasks by end date
            sort_by: Sort field
            reverse: Reverse sort order
            start_date: Chart display start date
            end_date: Chart display end date

        Returns:
            GanttOutput with Gantt chart data

        Note:
            filter_start_date/filter_end_date are for filtering tasks.
            start_date/end_date are for the chart display range.
        """
        params: dict[str, Any] = {
            "all": str(all).lower(),
            "sort": sort_by,
            "reverse": str(reverse).lower(),
        }

        # Add filter parameters if provided
        if status:
            params["status"] = status.lower()
        if tags:
            params["tags"] = tags
        if filter_start_date:
            params["filter_start_date"] = filter_start_date.isoformat()
        if filter_end_date:
            params["filter_end_date"] = filter_end_date.isoformat()

        # Add chart display range if provided
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        response = self._base._safe_request("get", "/api/v1/gantt", params=params)
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_gantt_output(data)

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics.

        Returns:
            TagStatisticsOutput with tag statistics
        """
        response = self._base._safe_request("get", "/api/v1/tags/statistics")
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        return convert_to_tag_statistics_output(data)
