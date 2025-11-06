"""HTTP API client for Taskdog server."""
# mypy: ignore-errors

from datetime import date, datetime
from typing import Any

import httpx  # type: ignore[import-not-found]

from application.dto.gantt_output import GanttOutput
from application.dto.get_task_by_id_output import GetTaskByIdOutput
from application.dto.optimization_output import OptimizationOutput
from application.dto.statistics_output import StatisticsOutput
from application.dto.tag_statistics_output import TagStatisticsOutput
from application.dto.task_detail_output import GetTaskDetailOutput
from application.dto.task_list_output import TaskListOutput
from application.dto.task_operation_output import TaskOperationOutput
from application.dto.update_task_output import UpdateTaskOutput
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from domain.services.holiday_checker import IHolidayChecker


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

        response = self.client.post("/api/v1/tasks", json=payload)
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

        response = self.client.patch(f"/api/v1/tasks/{task_id}", json=payload)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_update_task_output(data)

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive (soft delete) a task.

        Args:
            task_id: Task ID

        Returns:
            TaskOperationOutput with archived task data

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self.client.post(f"/api/v1/tasks/{task_id}/archive")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(f"/api/v1/tasks/{task_id}/restore")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def remove_task(self, task_id: int) -> None:
        """Permanently delete a task.

        Args:
            task_id: Task ID

        Raises:
            TaskNotFoundException: If task not found
        """
        response = self.client.delete(f"/api/v1/tasks/{task_id}")
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
        response = self.client.post(f"/api/v1/tasks/{task_id}/start")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(f"/api/v1/tasks/{task_id}/complete")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(f"/api/v1/tasks/{task_id}/pause")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(f"/api/v1/tasks/{task_id}/cancel")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(f"/api/v1/tasks/{task_id}/reopen")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

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
        response = self.client.post(
            f"/api/v1/tasks/{task_id}/dependencies", json={"depends_on_id": depends_on_id}
        )
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def remove_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
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
        response = self.client.delete(f"/api/v1/tasks/{task_id}/dependencies/{depends_on_id}")
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
        response = self.client.put(f"/api/v1/tasks/{task_id}/tags", json={"tags": tags})
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_task_operation_output(data)

    def log_hours(self, task_id: int, hours: float, date_str: str) -> TaskOperationOutput:
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
        response = self.client.post(
            f"/api/v1/tasks/{task_id}/log-hours", json={"hours": hours, "date": date_str}
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
        response = self.client.get(f"/api/v1/statistics?period={period}")
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

        response = self.client.post("/api/v1/optimize", json=payload)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_optimization_output(data)

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get available optimization algorithms.

        Returns:
            List of (name, display_name, description) tuples
        """
        response = self.client.get("/api/v1/algorithms")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return [(algo["name"], algo["display_name"], algo["description"]) for algo in data]

    # Query Controller methods

    def list_tasks(
        self, filter_obj: TaskFilter | None = None, sort_by: str = "id", reverse: bool = False
    ) -> TaskListOutput:
        """List tasks with optional filtering and sorting.

        Args:
            filter_obj: Task filter (NOT IMPLEMENTED for API)
            sort_by: Sort field
            reverse: Reverse sort order

        Returns:
            TaskListOutput with task list and metadata

        Note:
            filter_obj is not yet implemented for API client.
            Use query parameters instead for now.
        """
        params = {"sort": sort_by, "reverse": str(reverse).lower()}

        response = self.client.get("/api/v1/tasks", params=params)
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
        response = self.client.get(f"/api/v1/tasks/{task_id}")
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
        response = self.client.get(f"/api/v1/tasks/{task_id}")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_get_task_detail_output(data)

    def get_gantt_data(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
        holiday_checker: IHolidayChecker | None = None,
    ) -> GanttOutput:
        """Get Gantt chart data.

        Args:
            filter_obj: Task filter (NOT IMPLEMENTED for API)
            sort_by: Sort field
            reverse: Reverse sort order
            start_date: Chart start date
            end_date: Chart end date
            holiday_checker: Holiday checker (NOT USED for API)

        Returns:
            GanttOutput with Gantt chart data

        Note:
            filter_obj and holiday_checker are not yet implemented for API client.
        """
        params = {"sort": sort_by, "reverse": str(reverse).lower()}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        response = self.client.get("/api/v1/gantt", params=params)
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_gantt_output(data)

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics.

        Returns:
            TagStatisticsOutput with tag statistics
        """
        response = self.client.get("/api/v1/tags/statistics")
        if not response.is_success:
            self._handle_error(response)

        data = response.json()
        return self._convert_to_tag_statistics_output(data)

    # Conversion methods

    def _convert_to_task_operation_output(self, data: dict[str, Any]) -> TaskOperationOutput:
        """Convert API response to TaskOperationOutput."""
        return TaskOperationOutput(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data["status"]),
            priority=data["priority"],
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
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
        from application.dto.task_operation_output import TaskOperationOutput
        from application.dto.update_task_output import UpdateTaskOutput

        # Construct TaskOperationOutput from the response data
        task = TaskOperationOutput(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data["status"]),
            priority=data["priority"],
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
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
        """Convert API response to TaskListOutput."""
        # Simplified - full implementation would need to convert all task fields
        from application.dto.task_dto import TaskRowDto

        tasks = [
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
                deadline=datetime.fromisoformat(task["deadline"]) if task.get("deadline") else None,
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
            for task in data["tasks"]
        ]

        return TaskListOutput(
            tasks=tasks, total_count=data["total_count"], filtered_count=data["filtered_count"]
        )

    def _convert_to_get_task_by_id_output(self, data: dict[str, Any]) -> GetTaskByIdOutput:
        """Convert API response to GetTaskByIdOutput."""
        from datetime import date as date_type

        from application.dto.get_task_by_id_output import GetTaskByIdOutput
        from application.dto.task_dto import TaskDetailDto

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
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            estimated_duration=data.get("estimated_duration"),
            daily_allocations={
                date_type.fromisoformat(k): v for k, v in data.get("daily_allocations", {}).items()
            },
            is_fixed=data.get("is_fixed", False),
            depends_on=data.get("depends_on", []),
            actual_daily_hours={
                date_type.fromisoformat(k): v for k, v in data.get("actual_daily_hours", {}).items()
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

    def _convert_to_get_task_detail_output(self, data: dict[str, Any]) -> GetTaskDetailOutput:
        """Convert API response to GetTaskDetailOutput."""
        from datetime import date as date_type

        from application.dto.task_detail_output import GetTaskDetailOutput
        from application.dto.task_dto import TaskDetailDto

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
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            actual_start=datetime.fromisoformat(data["actual_start"])
            if data.get("actual_start")
            else None,
            actual_end=datetime.fromisoformat(data["actual_end"])
            if data.get("actual_end")
            else None,
            estimated_duration=data.get("estimated_duration"),
            daily_allocations={
                date_type.fromisoformat(k): v for k, v in data.get("daily_allocations", {}).items()
            },
            is_fixed=data.get("is_fixed", False),
            depends_on=data.get("depends_on", []),
            actual_daily_hours={
                date_type.fromisoformat(k): v for k, v in data.get("actual_daily_hours", {}).items()
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

        return GetTaskDetailOutput(task=task, notes_content=notes_content, has_notes=has_notes)

    def _convert_to_gantt_output(self, data: dict[str, Any]) -> GanttOutput:
        """Convert API response to GanttOutput."""
        from datetime import datetime

        from application.dto.gantt_output import GanttDateRange, GanttOutput
        from application.dto.task_dto import GanttTaskDto
        from domain.entities.task import TaskStatus

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
                    datetime.fromisoformat(task["planned_end"]) if task.get("planned_end") else None
                ),
                actual_start=(
                    datetime.fromisoformat(task["actual_start"])
                    if task.get("actual_start")
                    else None
                ),
                actual_end=(
                    datetime.fromisoformat(task["actual_end"]) if task.get("actual_end") else None
                ),
                deadline=(
                    datetime.fromisoformat(task["deadline"]) if task.get("deadline") else None
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
        holidays = {datetime.fromisoformat(date_str).date() for date_str in data["holidays"]}

        return GanttOutput(
            date_range=date_range,
            tasks=tasks,
            task_daily_hours=task_daily_hours,
            daily_workload=daily_workload,
            holidays=holidays,
        )

    def _convert_to_statistics_output(self, data: dict[str, Any]) -> StatisticsOutput:
        """Convert API response to StatisticsOutput."""
        # Simplified implementation
        raise NotImplementedError("calculate_statistics not yet implemented for API client")

    def _convert_to_optimization_output(self, data: dict[str, Any]) -> OptimizationOutput:
        """Convert API response to OptimizationOutput."""
        # Simplified implementation
        raise NotImplementedError("optimize_schedule not yet implemented for API client")

    def _convert_to_tag_statistics_output(self, data: dict[str, Any]) -> TagStatisticsOutput:
        """Convert API response to TagStatisticsOutput."""
        from application.dto.tag_statistics_output import TagStatisticsOutput

        # API returns: {tags: [{tag: str, count: int, completion_rate: float}], total_tags: int}
        # Convert to DTO: {tag_counts: dict[str, int], total_tags: int, total_tagged_tasks: int}
        tag_counts = {item["tag"]: item["count"] for item in data["tags"]}

        return TagStatisticsOutput(
            tag_counts=tag_counts,
            total_tags=data["total_tags"],
            total_tagged_tasks=0,  # Not available from API response
        )
