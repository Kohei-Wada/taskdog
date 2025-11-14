"""HTTP API client for Taskdog server."""
# mypy: ignore-errors

from datetime import date, datetime
from typing import Any

import httpx  # type: ignore[import-not-found]

from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import GetTaskByIdOutput
from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.statistics_output import StatisticsOutput
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import GetTaskDetailOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import UpdateTaskOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    ServerConnectionError,
    TaskNotFoundException,
    TaskValidationError,
)
from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class TaskdogApiClient:
    """HTTP client that mimics Controller interface.

    This client provides the same methods as the controllers but makes HTTP
    requests to the FastAPI server instead of calling controllers directly.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0):
        """Initialize API client.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self._has_notes_cache: dict[int, bool] = {}  # Cache for has_notes info

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "TaskdogApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: HTTP response

        Raises:
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400
            Exception: For other errors
        """
        if response.status_code == 404:
            detail = response.json().get("detail", "Task not found")
            raise TaskNotFoundException(detail)
        elif response.status_code == 400:
            detail = response.json().get("detail", "Validation error")
            raise TaskValidationError(detail)
        else:
            response.raise_for_status()

    def _safe_request(self, method: str, *args, **kwargs) -> httpx.Response:
        """Execute HTTP request with connection error handling.

        Args:
            method: HTTP method name ('get', 'post', 'patch', 'delete', 'put')
            *args: Positional arguments for the request
            **kwargs: Keyword arguments for the request

        Returns:
            HTTP response

        Raises:
            ServerConnectionError: If connection to server fails
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400
            Exception: For other errors
        """
        try:
            request_method = getattr(self.client, method)
            return request_method(*args, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            raise ServerConnectionError(self.base_url, e) from e

    # CRUD Controller methods

    def create_task(
        self,
        name: str,
        priority: int | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        tags: list[str] | None = None,
    ) -> TaskOperationOutput:
        """Create a new task.

        Args:
            name: Task name
            priority: Task priority
            deadline: Task deadline
            estimated_duration: Estimated duration in hours
            planned_start: Planned start datetime
            planned_end: Planned end datetime
            is_fixed: Whether schedule is fixed
            tags: List of tags

        Returns:
            TaskOperationOutput with created task data

        Raises:
            TaskValidationError: If validation fails
        """
        payload = {
            "name": name,
            "priority": priority,
            "deadline": deadline.isoformat() if deadline else None,
            "estimated_duration": estimated_duration,
            "planned_start": planned_start.isoformat() if planned_start else None,
            "planned_end": planned_end.isoformat() if planned_end else None,
            "is_fixed": is_fixed,
            "tags": tags,
        }

        response = self._safe_request("post", "/api/v1/tasks", json=payload)
        if response.status_code != 201:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def _build_update_payload(
        self,
        name: str | None,
        priority: int | None,
        status: TaskStatus | None,
        planned_start: datetime | None,
        planned_end: datetime | None,
        deadline: datetime | None,
        estimated_duration: float | None,
        is_fixed: bool | None,
        tags: list[str] | None,
    ) -> dict:
        """Build update task payload from optional parameters."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if priority is not None:
            payload["priority"] = priority
        if status is not None:
            payload["status"] = status.value
        if planned_start is not None:
            payload["planned_start"] = planned_start.isoformat()
        if planned_end is not None:
            payload["planned_end"] = planned_end.isoformat()
        if deadline is not None:
            payload["deadline"] = deadline.isoformat()
        if estimated_duration is not None:
            payload["estimated_duration"] = estimated_duration
        if is_fixed is not None:
            payload["is_fixed"] = is_fixed
        if tags is not None:
            payload["tags"] = tags
        return payload

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        priority: int | None = None,
        status: TaskStatus | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        is_fixed: bool | None = None,
        tags: list[str] | None = None,
    ) -> UpdateTaskOutput:
        """Update task fields.

        Args:
            task_id: Task ID
            name: New task name
            priority: New priority
            status: New status
            planned_start: New planned start
            planned_end: New planned end
            deadline: New deadline
            estimated_duration: New estimated duration
            is_fixed: New fixed status
            tags: New tags list

        Returns:
            UpdateTaskOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        payload = self._build_update_payload(
            name,
            priority,
            status,
            planned_start,
            planned_end,
            deadline,
            estimated_duration,
            is_fixed,
            tags,
        )

        response = self._safe_request("patch", f"/api/v1/tasks/{task_id}", json=payload)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_update_task_output(data)

    def _lifecycle_operation(self, task_id: int, operation: str) -> TaskOperationOutput:
        """Execute a lifecycle operation on a task.

        Generic helper for lifecycle operations (archive, restore, start, complete, etc.)
        that follow the same pattern.

        Args:
            task_id: Task ID
            operation: Operation name (e.g., "archive", "start", "complete")

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._safe_request("post", f"/api/v1/tasks/{task_id}/{operation}")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive (soft delete) a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with archived task data

        Raises:
            TaskNotFoundException: If task not found
        """
        return self._lifecycle_operation(task_id, "archive")

    def restore_task(self, task_id: int) -> TaskOperationOutput:
        """Restore an archived task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with restored task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If not archived
        """
        return self._lifecycle_operation(task_id, "restore")

    def remove_task(self, task_id: int) -> None:
        """Permanently delete a task.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request("delete", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._handle_error(response)

    # Lifecycle Controller methods

    def start_task(self, task_id: int) -> TaskOperationOutput:
        """Start a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "start")

    def complete_task(self, task_id: int) -> TaskOperationOutput:
        """Complete a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "complete")

    def pause_task(self, task_id: int) -> TaskOperationOutput:
        """Pause a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "pause")

    def cancel_task(self, task_id: int) -> TaskOperationOutput:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "cancel")

    def reopen_task(self, task_id: int) -> TaskOperationOutput:
        """Reopen a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        return self._lifecycle_operation(task_id, "reopen")

    # Relationship Controller methods

    def add_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Add a dependency to a task.

        Args:
            task_id: Task ID
            depends_on_id: ID of task to depend on

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails (e.g., circular dependency)
        """
        response = self._safe_request(
            "post",
            f"/api/v1/tasks/{task_id}/dependencies",
            json={"depends_on_id": depends_on_id},
        )
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def remove_dependency(
        self, task_id: int, depends_on_id: int
    ) -> TaskOperationOutput:
        """Remove a dependency from a task.

        Args:
            task_id: Task ID
            depends_on_id: Dependency ID to remove

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._safe_request(
            "delete", f"/api/v1/tasks/{task_id}/dependencies/{depends_on_id}"
        )
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def set_task_tags(self, task_id: int, tags: list[str]) -> TaskOperationOutput:
        """Set task tags (replaces existing tags).

        Args:
            task_id: Task ID
            tags: New tags list

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._safe_request(
            "put", f"/api/v1/tasks/{task_id}/tags", json={"tags": tags}
        )
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def log_hours(
        self, task_id: int, hours: float, date_str: str
    ) -> TaskOperationOutput:
        """Log actual hours worked on a task.

        Args:
            task_id: Task ID
            hours: Hours worked
            date_str: Date in ISO format

        Returns:
            TaskOperationOutput with updated task data

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails
        """
        response = self._safe_request(
            "post",
            f"/api/v1/tasks/{task_id}/log-hours",
            json={"hours": hours, "date": date_str},
        )
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    # Analytics Controller methods

    def calculate_statistics(self, period: str = "all") -> StatisticsOutput:
        """Calculate task statistics.

        Args:
            period: Time period (all, 7d, 30d)

        Returns:
            StatisticsOutput with statistics data

        Raises:
            TaskValidationError: If period is invalid
        """
        response = self._safe_request("get", f"/api/v1/statistics?period={period}")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_statistics_output(data)

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool = True,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Algorithm name
            start_date: Optimization start date
            max_hours_per_day: Maximum hours per day
            force_override: Force override existing schedules

        Returns:
            OptimizationOutput with optimization results

        Raises:
            TaskValidationError: If validation fails
        """
        payload = {
            "algorithm": algorithm,
            "start_date": start_date.isoformat(),
            "max_hours_per_day": max_hours_per_day,
            "force_override": force_override,
        }

        response = self._safe_request("post", "/api/v1/optimize", json=payload)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_optimization_output(data)

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get available optimization algorithms.

        Returns:
            List of (name, display_name, description) tuples
        """
        response = self._safe_request("get", "/api/v1/algorithms")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return [
            (algo["name"], algo["display_name"], algo["description"]) for algo in data
        ]

    # Query Controller methods

    def _parse_filter_to_params_legacy(self, filter_obj) -> dict[str, any]:
        """Parse TaskFilter object to query parameters (legacy support for TUI).

        This is a temporary backward compatibility method for TUI.
        CLI commands should use the new direct parameter API.

        Args:
            filter_obj: TaskFilter object or None

        Returns:
            Dictionary with extracted parameters
        """
        from taskdog_core.application.queries.filters.date_range_filter import (
            DateRangeFilter,
        )
        from taskdog_core.application.queries.filters.non_archived_filter import (
            NonArchivedFilter,
        )
        from taskdog_core.application.queries.filters.status_filter import StatusFilter
        from taskdog_core.application.queries.filters.tag_filter import TagFilter

        params = {
            "all": True,
            "status": None,
            "tags": None,
            "start_date": None,
            "end_date": None,
        }

        if filter_obj:
            current_filter = filter_obj
            while current_filter:
                if isinstance(current_filter, NonArchivedFilter):
                    params["all"] = False
                elif isinstance(current_filter, StatusFilter):
                    params["status"] = current_filter.status.value.lower()
                elif isinstance(current_filter, TagFilter):
                    params["tags"] = current_filter.tags
                elif isinstance(current_filter, DateRangeFilter):
                    params["start_date"] = current_filter.start_date
                    params["end_date"] = current_filter.end_date

                current_filter = getattr(current_filter, "_next", None)

        return params

    def list_tasks(
        self,
        filter_obj=None,  # Legacy parameter for TUI compatibility
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
        holiday_checker: IHolidayChecker | None = None,
    ) -> TaskListOutput:
        """List tasks with optional filtering and sorting.

        Args:
            filter_obj: (DEPRECATED, TUI only) TaskFilter object for backward compatibility
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
            holiday_checker: Holiday checker (ignored for API - server handles holidays)

        Returns:
            TaskListOutput with task list and metadata, optionally including Gantt data

        Note:
            holiday_checker is ignored in API mode (server handles holidays).
            filter_obj is deprecated and only supported for TUI backward compatibility.
        """
        # Handle legacy filter_obj parameter (TUI compatibility)
        if filter_obj is not None:
            legacy_params = self._parse_filter_to_params_legacy(filter_obj)
            all = legacy_params["all"]
            status = legacy_params["status"] or status
            tags = legacy_params["tags"] or tags
            start_date = legacy_params["start_date"] or start_date
            end_date = legacy_params["end_date"] or end_date

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

        response = self._safe_request("get", "/api/v1/tasks", params=params)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_list_output(data)

    def get_task_by_id(self, task_id: int) -> GetTaskByIdOutput:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            GetTaskByIdOutput with task data

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request("get", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_get_task_by_id_output(data)

    def get_task_detail(self, task_id: int) -> GetTaskDetailOutput:
        """Get task details with notes.

        Args:
            task_id: Task ID

        Returns:
            GetTaskDetailOutput with task data and notes

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request("get", f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_get_task_detail_output(data)

    def get_gantt_data(
        self,
        filter_obj=None,  # Legacy parameter for TUI compatibility
        all: bool = False,
        status: str | None = None,
        tags: list[str] | None = None,
        filter_start_date: date | None = None,
        filter_end_date: date | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
        holiday_checker: IHolidayChecker | None = None,
    ) -> GanttOutput:
        """Get Gantt chart data.

        Args:
            filter_obj: (DEPRECATED, TUI only) TaskFilter object for backward compatibility
            all: Include archived tasks (default: False)
            status: Filter by status
            tags: Filter by tags (OR logic)
            filter_start_date: Filter tasks by start date
            filter_end_date: Filter tasks by end date
            sort_by: Sort field
            reverse: Reverse sort order
            start_date: Chart display start date
            end_date: Chart display end date
            holiday_checker: Holiday checker (ignored for API - server handles holidays)

        Returns:
            GanttOutput with Gantt chart data

        Note:
            holiday_checker is ignored in API mode (server handles holidays).
            filter_start_date/filter_end_date are for filtering tasks.
            start_date/end_date are for the chart display range.
            filter_obj is deprecated and only supported for TUI backward compatibility.
        """
        # Handle legacy filter_obj parameter (TUI compatibility)
        if filter_obj is not None:
            legacy_params = self._parse_filter_to_params_legacy(filter_obj)
            all = legacy_params["all"]
            status = legacy_params["status"] or status
            tags = legacy_params["tags"] or tags
            filter_start_date = legacy_params["start_date"] or filter_start_date
            filter_end_date = legacy_params["end_date"] or filter_end_date

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

        response = self._safe_request("get", "/api/v1/gantt", params=params)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_gantt_output(data)

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics.

        Returns:
            TagStatisticsOutput with tag statistics
        """
        response = self._safe_request("get", "/api/v1/tags/statistics")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_tag_statistics_output(data)

    # Conversion methods

    def _convert_to_task_operation_output(
        self, data: dict[str, Any]
    ) -> TaskOperationOutput:
        """Convert API response to TaskOperationOutput."""
        return TaskOperationOutput(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data["status"]),
            priority=data["priority"],
            deadline=datetime.fromisoformat(data["deadline"])
            if data.get("deadline")
            else None,
            estimated_duration=data.get("estimated_duration"),
            planned_start=datetime.fromisoformat(data["planned_start"])
            if data.get("planned_start")
            else None,
            planned_end=datetime.fromisoformat(data["planned_end"])
            if data.get("planned_end")
            else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            depends_on=data.get("depends_on", []),
            tags=data.get("tags", []),
            is_fixed=data.get("is_fixed", False),
            is_archived=data.get("is_archived", False),
            actual_duration_hours=data.get("actual_duration_hours"),
            actual_daily_hours=data.get("actual_daily_hours", {}),
        )

    def _convert_to_update_task_output(self, data: dict[str, Any]) -> UpdateTaskOutput:
        """Convert API response to UpdateTaskOutput."""
        from taskdog_core.application.dto.task_operation_output import (
            TaskOperationOutput,
        )
        from taskdog_core.application.dto.update_task_output import UpdateTaskOutput

        # Construct TaskOperationOutput from the response data
        task = TaskOperationOutput(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data["status"]),
            priority=data["priority"],
            deadline=datetime.fromisoformat(data["deadline"])
            if data.get("deadline")
            else None,
            estimated_duration=data.get("estimated_duration"),
            planned_start=datetime.fromisoformat(data["planned_start"])
            if data.get("planned_start")
            else None,
            planned_end=datetime.fromisoformat(data["planned_end"])
            if data.get("planned_end")
            else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            depends_on=data.get("depends_on", []),
            tags=data.get("tags", []),
            is_fixed=data.get("is_fixed", False),
            is_archived=data.get("is_archived", False),
            actual_duration_hours=data.get("actual_duration_hours"),
            actual_daily_hours=data.get("actual_daily_hours", {}),
        )

        # Construct UpdateTaskOutput with nested task and updated_fields
        return UpdateTaskOutput(
            task=task,
            updated_fields=data.get("updated_fields", []),
        )

    def _convert_to_task_list_output(self, data: dict[str, Any]) -> TaskListOutput:
        """Convert API response to TaskListOutput.

        Caches has_notes information from the API response for later use.
        """
        # Simplified - full implementation would need to convert all task fields
        from taskdog_core.application.dto.task_dto import TaskRowDto

        tasks = []
        for task in data["tasks"]:
            # Cache has_notes information
            self._has_notes_cache[task["id"]] = task.get("has_notes", False)

            tasks.append(
                TaskRowDto(
                    id=task["id"],
                    name=task["name"],
                    priority=task["priority"],
                    status=TaskStatus(task["status"]),
                    planned_start=datetime.fromisoformat(task["planned_start"])
                    if task.get("planned_start")
                    else None,
                    planned_end=datetime.fromisoformat(task["planned_end"])
                    if task.get("planned_end")
                    else None,
                    deadline=datetime.fromisoformat(task["deadline"])
                    if task.get("deadline")
                    else None,
                    actual_start=datetime.fromisoformat(task["actual_start"])
                    if task.get("actual_start")
                    else None,
                    actual_end=datetime.fromisoformat(task["actual_end"])
                    if task.get("actual_end")
                    else None,
                    estimated_duration=task.get("estimated_duration"),
                    actual_duration_hours=task.get("actual_duration_hours"),
                    is_fixed=task.get("is_fixed", False),
                    depends_on=task.get("depends_on", []),
                    tags=task.get("tags", []),
                    is_archived=task.get("is_archived", False),
                    is_finished=task.get("is_finished", False),
                    created_at=datetime.fromisoformat(task["created_at"]),
                    updated_at=datetime.fromisoformat(task["updated_at"]),
                )
            )

        # Convert gantt data if present
        gantt_data = None
        if data.get("gantt"):
            gantt_data = self._convert_to_gantt_output(data["gantt"])

        return TaskListOutput(
            tasks=tasks,
            total_count=data["total_count"],
            filtered_count=data["filtered_count"],
            gantt_data=gantt_data,
        )

    def _convert_to_get_task_by_id_output(
        self, data: dict[str, Any]
    ) -> GetTaskByIdOutput:
        """Convert API response to GetTaskByIdOutput."""
        from datetime import date as date_type

        from taskdog_core.application.dto.get_task_by_id_output import GetTaskByIdOutput
        from taskdog_core.application.dto.task_dto import TaskDetailDto

        # Convert task data (same as get_task_detail but without notes)
        task = TaskDetailDto(
            id=data["id"],
            name=data["name"],
            priority=data["priority"],
            status=TaskStatus(data["status"]),
            planned_start=datetime.fromisoformat(data["planned_start"])
            if data.get("planned_start")
            else None,
            planned_end=datetime.fromisoformat(data["planned_end"])
            if data.get("planned_end")
            else None,
            deadline=datetime.fromisoformat(data["deadline"])
            if data.get("deadline")
            else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            estimated_duration=data.get("estimated_duration"),
            daily_allocations={
                date_type.fromisoformat(k): v
                for k, v in data.get("daily_allocations", {}).items()
            },
            is_fixed=data.get("is_fixed", False),
            depends_on=data.get("depends_on", []),
            actual_daily_hours={
                date_type.fromisoformat(k): v
                for k, v in data.get("actual_daily_hours", {}).items()
            },
            tags=data.get("tags", []),
            is_archived=data.get("is_archived", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            actual_duration_hours=data.get("actual_duration_hours"),
            is_active=data.get("is_active", False),
            is_finished=data.get("is_finished", False),
            can_be_modified=data.get("can_be_modified", False),
            is_schedulable=data.get("is_schedulable", False),
        )

        return GetTaskByIdOutput(task=task)

    def _convert_to_get_task_detail_output(
        self, data: dict[str, Any]
    ) -> GetTaskDetailOutput:
        """Convert API response to GetTaskDetailOutput."""
        from datetime import date as date_type

        from taskdog_core.application.dto.task_detail_output import GetTaskDetailOutput
        from taskdog_core.application.dto.task_dto import TaskDetailDto

        # Convert task data
        task = TaskDetailDto(
            id=data["id"],
            name=data["name"],
            priority=data["priority"],
            status=TaskStatus(data["status"]),
            planned_start=datetime.fromisoformat(data["planned_start"])
            if data.get("planned_start")
            else None,
            planned_end=datetime.fromisoformat(data["planned_end"])
            if data.get("planned_end")
            else None,
            deadline=datetime.fromisoformat(data["deadline"])
            if data.get("deadline")
            else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            estimated_duration=data.get("estimated_duration"),
            daily_allocations={
                date_type.fromisoformat(k): v
                for k, v in data.get("daily_allocations", {}).items()
            },
            is_fixed=data.get("is_fixed", False),
            depends_on=data.get("depends_on", []),
            actual_daily_hours={
                date_type.fromisoformat(k): v
                for k, v in data.get("actual_daily_hours", {}).items()
            },
            tags=data.get("tags", []),
            is_archived=data.get("is_archived", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            actual_duration_hours=data.get("actual_duration_hours"),
            is_active=data.get("is_active", False),
            is_finished=data.get("is_finished", False),
            can_be_modified=data.get("can_be_modified", False),
            is_schedulable=data.get("is_schedulable", False),
        )

        # Extract notes
        notes_content = data.get("notes")
        has_notes = notes_content is not None and notes_content != ""

        return GetTaskDetailOutput(
            task=task, notes_content=notes_content, has_notes=has_notes
        )

    def _convert_to_gantt_output(self, data: dict[str, Any]) -> GanttOutput:
        """Convert API response to GanttOutput."""
        from datetime import datetime

        from taskdog_core.application.dto.gantt_output import (
            GanttDateRange,
            GanttOutput,
        )
        from taskdog_core.application.dto.task_dto import GanttTaskDto
        from taskdog_core.domain.entities.task import TaskStatus

        # Convert date_range
        date_range = GanttDateRange(
            start_date=datetime.fromisoformat(data["date_range"]["start_date"]).date(),
            end_date=datetime.fromisoformat(data["date_range"]["end_date"]).date(),
        )

        # Convert tasks (list[GanttTaskResponse] -> list[GanttTaskDto])
        tasks = [
            GanttTaskDto(
                id=task["id"],
                name=task["name"],
                status=TaskStatus[task["status"].upper()],
                estimated_duration=task.get("estimated_duration"),
                planned_start=(
                    datetime.fromisoformat(task["planned_start"])
                    if task.get("planned_start")
                    else None
                ),
                planned_end=(
                    datetime.fromisoformat(task["planned_end"])
                    if task.get("planned_end")
                    else None
                ),
                actual_start=(
                    datetime.fromisoformat(task["actual_start"])
                    if task.get("actual_start")
                    else None
                ),
                actual_end=(
                    datetime.fromisoformat(task["actual_end"])
                    if task.get("actual_end")
                    else None
                ),
                deadline=(
                    datetime.fromisoformat(task["deadline"])
                    if task.get("deadline")
                    else None
                ),
                is_finished=task["status"].upper() in ["COMPLETED", "CANCELED"],
            )
            for task in data["tasks"]
        ]

        # Convert task_daily_hours: dict[str, dict[str, float]] -> dict[int, dict[date, float]]
        task_daily_hours = {
            int(task_id): {
                datetime.fromisoformat(date_str).date(): hours
                for date_str, hours in daily_hours.items()
            }
            for task_id, daily_hours in data["task_daily_hours"].items()
        }

        # Convert daily_workload: dict[str, float] -> dict[date, float]
        daily_workload = {
            datetime.fromisoformat(date_str).date(): hours
            for date_str, hours in data["daily_workload"].items()
        }

        # Convert holidays: list[str] -> set[date]
        holidays = {
            datetime.fromisoformat(date_str).date() for date_str in data["holidays"]
        }

        return GanttOutput(
            date_range=date_range,
            tasks=tasks,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
            holidays=holidays,
        )

    def _convert_to_statistics_output(self, data: dict[str, Any]) -> StatisticsOutput:
        """Convert API response to StatisticsOutput.

        Args:
            data: API response data with format:
                {
                    "completion": {...},
                    "time": {...} | None,
                    "estimation": {...} | None,
                    "deadline": {...} | None,
                    "priority": {...},
                    "trends": {...} | None
                }

        Returns:
            StatisticsOutput with converted data
        """
        from taskdog_core.application.dto.statistics_output import (
            DeadlineComplianceStatistics,
            EstimationAccuracyStatistics,
            PriorityDistributionStatistics,
            StatisticsOutput,
            TaskStatistics,
            TimeStatistics,
            TrendStatistics,
        )

        # Convert completion statistics (always present)
        completion = data["completion"]
        task_stats = TaskStatistics(
            total_tasks=completion["total"],
            pending_count=completion["pending"],
            in_progress_count=completion["in_progress"],
            completed_count=completion["completed"],
            canceled_count=completion["canceled"],
            completion_rate=completion["completion_rate"],
        )

        # Convert time statistics (optional)
        time_stats = None
        if data.get("time"):
            time = data["time"]
            time_stats = TimeStatistics(
                total_work_hours=time["total_logged_hours"],
                average_work_hours=time.get("average_task_duration") or 0.0,
                median_work_hours=0.0,  # Not available in API response
                longest_task=None,  # Not available in API response
                shortest_task=None,  # Not available in API response
                tasks_with_time_tracking=0,  # Not available in API response
            )

        # Convert estimation statistics (optional)
        estimation_stats = None
        if data.get("estimation"):
            estimation = data["estimation"]
            estimation_stats = EstimationAccuracyStatistics(
                total_tasks_with_estimation=estimation["tasks_with_estimates"],
                accuracy_rate=estimation["average_deviation_percentage"] / 100,
                over_estimated_count=0,  # Not available in API response
                under_estimated_count=0,  # Not available in API response
                exact_count=0,  # Not available in API response
                best_estimated_tasks=[],  # Not available in API response
                worst_estimated_tasks=[],  # Not available in API response
            )

        # Convert deadline statistics (optional)
        deadline_stats = None
        if data.get("deadline"):
            deadline = data["deadline"]
            deadline_stats = DeadlineComplianceStatistics(
                total_tasks_with_deadline=deadline["met"] + deadline["missed"],
                met_deadline_count=deadline["met"],
                missed_deadline_count=deadline["missed"],
                compliance_rate=deadline["adherence_rate"],
                average_delay_days=0.0,  # Not available in API response
            )

        # Convert priority statistics (always present)
        priority = data["priority"]
        priority_stats = PriorityDistributionStatistics(
            high_priority_count=sum(
                count
                for prio, count in priority["distribution"].items()
                if int(prio) >= 70
            ),
            medium_priority_count=sum(
                count
                for prio, count in priority["distribution"].items()
                if 30 <= int(prio) < 70
            ),
            low_priority_count=sum(
                count
                for prio, count in priority["distribution"].items()
                if int(prio) < 30
            ),
            high_priority_completion_rate=0.0,  # Not available in API response
            priority_completion_map={
                int(k): v for k, v in priority["distribution"].items()
            },
        )

        # Convert trend statistics (optional)
        trend_stats = None
        if data.get("trends"):
            trends = data["trends"]
            # Calculate last 7 and 30 days from completed_per_day
            completed_per_day = trends.get("completed_per_day", {})
            last_7_days = (
                sum(list(completed_per_day.values())[-7:]) if completed_per_day else 0
            )
            last_30_days = (
                sum(list(completed_per_day.values())[-30:]) if completed_per_day else 0
            )

            trend_stats = TrendStatistics(
                last_7_days_completed=last_7_days,
                last_30_days_completed=last_30_days,
                weekly_completion_trend={},  # Would need grouping logic
                monthly_completion_trend={},  # Would need grouping logic
            )

        return StatisticsOutput(
            task_stats=task_stats,
            time_stats=time_stats,
            estimation_stats=estimation_stats,
            deadline_stats=deadline_stats,
            priority_stats=priority_stats,
            trend_stats=trend_stats,
        )

    def _convert_to_optimization_output(
        self, data: dict[str, Any]
    ) -> OptimizationOutput:
        """Convert API response to OptimizationOutput.

        Args:
            data: API response data with format:
                {
                    "summary": {
                        "total_tasks": int,
                        "scheduled_tasks": int,
                        "failed_tasks": int,
                        "total_hours": float,
                        "start_date": str (ISO),
                        "end_date": str (ISO),
                        "algorithm": str
                    },
                    "failures": [{
                        "task_id": int,
                        "task_name": str,
                        "reason": str
                    }],
                    "message": str
                }

        Returns:
            OptimizationOutput with all optimization results
        """
        from datetime import date, datetime

        from taskdog_core.application.dto.optimization_output import (
            OptimizationOutput,
            SchedulingFailure,
        )
        from taskdog_core.application.dto.optimization_summary import (
            OptimizationSummary,
        )
        from taskdog_core.application.dto.task_dto import TaskSummaryDto

        # Parse summary
        summary_data = data["summary"]

        # Calculate days span from start_date and end_date
        start_date = date.fromisoformat(summary_data["start_date"])
        end_date = date.fromisoformat(summary_data["end_date"])
        days_span = (end_date - start_date).days + 1

        # Create TaskSummaryDto objects for unscheduled tasks from failures
        unscheduled_tasks = [
            TaskSummaryDto(id=f["task_id"], name=f["task_name"])
            for f in data["failures"]
        ]

        summary = OptimizationSummary(
            new_count=summary_data["scheduled_tasks"],
            rescheduled_count=0,  # API doesn't distinguish between new and rescheduled
            total_hours=summary_data["total_hours"],
            deadline_conflicts=0,  # Not provided by API
            days_span=days_span,
            unscheduled_tasks=unscheduled_tasks,
            overloaded_days=[],  # Not provided by API
        )

        # Parse failures
        failures = [
            SchedulingFailure(
                task=TaskSummaryDto(id=f["task_id"], name=f["task_name"]),
                reason=f["reason"],
            )
            for f in data["failures"]
        ]

        # Note: API response doesn't include successful_tasks details
        # We'll create minimal TaskSummaryDto objects
        successful_count = summary_data["scheduled_tasks"]
        successful_tasks = [
            TaskSummaryDto(id=i, name=f"Task {i}") for i in range(successful_count)
        ]

        # Daily allocations - not provided in response, use empty dict
        daily_allocations: dict[date, float] = {}

        # Task states before - not provided in response, use empty dict
        task_states_before: dict[int, datetime | None] = {}

        return OptimizationOutput(
            successful_tasks=successful_tasks,
            failed_tasks=failures,
            daily_allocations=daily_allocations,
            summary=summary,
            task_states_before=task_states_before,
        )

    def _convert_to_tag_statistics_output(
        self, data: dict[str, Any]
    ) -> TagStatisticsOutput:
        """Convert API response to TagStatisticsOutput."""
        from taskdog_core.application.dto.tag_statistics_output import (
            TagStatisticsOutput,
        )

        # API returns: {tags: [{tag: str, count: int, completion_rate: float}], total_tags: int}
        # Convert to DTO: {tag_counts: dict[str, int], total_tags: int, total_tagged_tasks: int}
        tag_counts = {item["tag"]: item["count"] for item in data["tags"]}

        return TagStatisticsOutput(
            tag_counts=tag_counts,
            total_tags=data["total_tags"],
            total_tagged_tasks=0,  # Not available from API response
        )

    # Notes methods

    def get_task_notes(self, task_id: int) -> tuple[str, bool]:
        """Get task notes.

        Args:
            task_id: Task ID

        Returns:
            Tuple of (notes_content, has_notes)

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request("get", f"/api/v1/tasks/{task_id}/notes")
        if response.status_code != 200:
            self._handle_error(response)
        data = response.json()
        return data["content"], data["has_notes"]

    def update_task_notes(self, task_id: int, content: str) -> None:
        """Update task notes.

        Args:
            task_id: Task ID
            content: Notes content (markdown)

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request(
            "put", f"/api/v1/tasks/{task_id}/notes", json={"content": content}
        )
        if response.status_code != 200:
            self._handle_error(response)

    def delete_task_notes(self, task_id: int) -> None:
        """Delete task notes.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self._safe_request("delete", f"/api/v1/tasks/{task_id}/notes")
        if response.status_code != 204:
            self._handle_error(response)

    def has_task_notes(self, task_id: int) -> bool:
        """Check if task has notes.

        Uses cached information from list_tasks if available, otherwise queries API.

        Args:
            task_id: Task ID

        Returns:
            True if task has notes, False otherwise

        Raises:
            TaskNotFoundException: If task not found
        """
        # Use cache if available (populated by list_tasks)
        if task_id in self._has_notes_cache:
            return self._has_notes_cache[task_id]

        # Fall back to API call
        _, has_notes = self.get_task_notes(task_id)
        self._has_notes_cache[task_id] = has_notes
        return has_notes
