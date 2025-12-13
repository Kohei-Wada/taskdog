"""Unified API client facade for Taskdog server communication.

This module provides backward compatibility by delegating to specialized
clients while maintaining the same public API.
"""

from datetime import date, datetime
from typing import Any

import httpx  # type: ignore[import-not-found]
from taskdog_client import (  # type: ignore[import-not-found]
    AnalyticsClient,
    AuditClient,
    BaseApiClient,
    LifecycleClient,
    NotesClient,
    QueryClient,
    RelationshipClient,
    TaskClient,
)

from taskdog_core.application.dto.audit_log_dto import AuditLogListOutput
from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.statistics_output import StatisticsOutput
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import TaskStatus


class TaskdogApiClient:
    """Main API client facade providing unified interface.

    Delegates to specialized clients while maintaining the same
    public API for backward compatibility.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        api_key: str | None = None,
    ):
        """Initialize API client.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
            api_key: API key for authentication (sent as X-Api-Key header)
        """
        self.base_url = base_url
        self._base = BaseApiClient(base_url, timeout, api_key=api_key)
        self._has_notes_cache: dict[int, bool] = {}

        # Initialize specialized clients
        self._tasks = TaskClient(self._base)
        self._lifecycle = LifecycleClient(self._base)
        self._relationships = RelationshipClient(self._base)
        self._queries = QueryClient(self._base, self._has_notes_cache)
        self._analytics = AnalyticsClient(self._base)
        self._notes = NotesClient(self._base)
        self._audit = AuditClient(self._base)

        # Share the notes cache with notes client
        self._notes._has_notes_cache = self._has_notes_cache

    @property
    def client(self) -> httpx.Client:
        """Access underlying httpx client for backward compatibility.

        Returns:
            The underlying httpx.Client instance
        """
        return self._base.client

    @property
    def client_id(self) -> str | None:
        """Get the client ID used for WebSocket message attribution.

        Returns:
            The client ID string, or None if not set
        """
        return self._base.client_id

    @property
    def api_key(self) -> str | None:
        """Get the API key used for authentication.

        Returns:
            The API key string, or None if not set
        """
        return self._base.api_key

    def set_client_id(self, client_id: str) -> None:
        """Set the client ID for WebSocket message attribution.

        Args:
            client_id: Client ID to set
        """
        self._base.client_id = client_id

    def close(self) -> None:
        """Close the HTTP client."""
        self._base.close()

    def __enter__(self) -> "TaskdogApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def check_health(self) -> bool:
        """Check if API server is reachable.

        Returns:
            True if server responds to health check, False otherwise
        """
        try:
            response = self._base._safe_request("get", "/health")
            return response.status_code == 200
        except Exception:
            return False

    # CRUD Controller methods - delegate to TaskClient

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
        """Create a new task."""
        return self._tasks.create_task(
            name,
            priority,
            deadline,
            estimated_duration,
            planned_start,
            planned_end,
            is_fixed,
            tags,
        )

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
    ) -> TaskUpdateOutput:
        """Update task fields."""
        return self._tasks.update_task(
            task_id,
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

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive (soft delete) a task."""
        return self._tasks.archive_task(task_id)

    def restore_task(self, task_id: int) -> TaskOperationOutput:
        """Restore an archived task."""
        return self._tasks.restore_task(task_id)

    def remove_task(self, task_id: int) -> None:
        """Permanently delete a task."""
        return self._tasks.remove_task(task_id)

    # Lifecycle Controller methods - delegate to LifecycleClient

    def start_task(self, task_id: int) -> TaskOperationOutput:
        """Start a task."""
        return self._lifecycle.start_task(task_id)

    def complete_task(self, task_id: int) -> TaskOperationOutput:
        """Complete a task."""
        return self._lifecycle.complete_task(task_id)

    def pause_task(self, task_id: int) -> TaskOperationOutput:
        """Pause a task."""
        return self._lifecycle.pause_task(task_id)

    def cancel_task(self, task_id: int) -> TaskOperationOutput:
        """Cancel a task."""
        return self._lifecycle.cancel_task(task_id)

    def reopen_task(self, task_id: int) -> TaskOperationOutput:
        """Reopen a task."""
        return self._lifecycle.reopen_task(task_id)

    def fix_actual_times(
        self,
        task_id: int,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        actual_duration: float | None = None,
        clear_start: bool = False,
        clear_end: bool = False,
        clear_duration: bool = False,
    ) -> TaskOperationOutput:
        """Fix actual start/end timestamps and/or duration for a task."""
        return self._lifecycle.fix_actual_times(
            task_id,
            actual_start,
            actual_end,
            actual_duration,
            clear_start,
            clear_end,
            clear_duration,
        )

    # Relationship Controller methods - delegate to RelationshipClient

    def add_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Add a dependency to a task."""
        return self._relationships.add_dependency(task_id, depends_on_id)

    def remove_dependency(
        self, task_id: int, depends_on_id: int
    ) -> TaskOperationOutput:
        """Remove a dependency from a task."""
        return self._relationships.remove_dependency(task_id, depends_on_id)

    def set_task_tags(self, task_id: int, tags: list[str]) -> TaskOperationOutput:
        """Set task tags (replaces existing tags)."""
        return self._relationships.set_task_tags(task_id, tags)

    # Analytics Controller methods - delegate to AnalyticsClient

    def calculate_statistics(self, period: str = "all") -> StatisticsOutput:
        """Calculate task statistics."""
        return self._analytics.calculate_statistics(period)

    def optimize_schedule(
        self,
        algorithm: str | None,
        start_date: datetime,
        max_hours_per_day: float | None,
        force_override: bool = True,
        task_ids: list[int] | None = None,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Optimization algorithm (None = server default)
            start_date: Start date for optimization
            max_hours_per_day: Max hours per day (None = server default)
            force_override: Force override existing schedules
            task_ids: Specific task IDs to optimize

        Returns:
            OptimizationOutput with results
        """
        return self._analytics.optimize_schedule(
            algorithm, start_date, max_hours_per_day, force_override, task_ids
        )

    def get_algorithm_metadata(self) -> list[tuple[str, str, str]]:
        """Get available optimization algorithms."""
        return self._analytics.get_algorithm_metadata()

    # Query Controller methods - delegate to QueryClient

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
        """List tasks with optional filtering and sorting."""
        return self._queries.list_tasks(
            all,
            status,
            tags,
            start_date,
            end_date,
            sort_by,
            reverse,
            include_gantt,
            gantt_start_date,
            gantt_end_date,
        )

    def list_today_tasks(
        self,
        all: bool = False,
        status: str | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
    ) -> TaskListOutput:
        """List tasks relevant for today."""
        return self._queries.list_today_tasks(all, status, sort_by, reverse)

    def list_week_tasks(
        self,
        all: bool = False,
        status: str | None = None,
        sort_by: str = "deadline",
        reverse: bool = False,
    ) -> TaskListOutput:
        """List tasks relevant for this week."""
        return self._queries.list_week_tasks(all, status, sort_by, reverse)

    def get_task_by_id(self, task_id: int) -> TaskByIdOutput:
        """Get task by ID."""
        return self._queries.get_task_by_id(task_id)

    def get_task_detail(self, task_id: int) -> TaskDetailOutput:
        """Get task details with notes."""
        return self._queries.get_task_detail(task_id)

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
        """Get Gantt chart data."""
        return self._queries.get_gantt_data(
            all,
            status,
            tags,
            filter_start_date,
            filter_end_date,
            sort_by,
            reverse,
            start_date,
            end_date,
        )

    def get_tag_statistics(self) -> TagStatisticsOutput:
        """Get tag statistics."""
        return self._queries.get_tag_statistics()

    # Notes methods - delegate to NotesClient

    def get_task_notes(self, task_id: int) -> tuple[str, bool]:
        """Get task notes."""
        return self._notes.get_task_notes(task_id)

    def update_task_notes(self, task_id: int, content: str) -> None:
        """Update task notes."""
        return self._notes.update_task_notes(task_id, content)

    def delete_task_notes(self, task_id: int) -> None:
        """Delete task notes."""
        return self._notes.delete_task_notes(task_id)

    def has_task_notes(self, task_id: int) -> bool:
        """Check if task has notes."""
        return self._notes.has_task_notes(task_id)

    # Audit log methods - delegate to AuditClient

    def list_audit_logs(
        self,
        client_filter: str | None = None,
        operation: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        success: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditLogListOutput:
        """List audit logs with optional filtering."""
        return self._audit.list_audit_logs(
            client_filter=client_filter,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
