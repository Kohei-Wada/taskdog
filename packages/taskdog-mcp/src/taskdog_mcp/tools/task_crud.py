"""Task CRUD MCP tools.

Tools for creating, reading, updating, and deleting tasks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskdog_mcp.tools.serializers import (
    iso,
    parse_iso_datetime,
    str_list,
    task_result,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register task CRUD tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def list_tasks(
        include_archived: bool = False,
        status: str | None = None,
        tags: list[str] | None = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> dict[str, Any]:
        """List all tasks with optional filtering.

        Args:
            include_archived: Include archived tasks (default: False)
            status: Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELED)
            tags: Filter by tags (OR logic)
            sort_by: Sort field (id, name, priority, deadline, status)
            reverse: Reverse sort order

        Returns:
            Dictionary with tasks list and metadata
        """
        result = client.list_tasks(
            include_archived=include_archived,
            status=status,
            tags=tags,
            sort_by=sort_by,
            reverse=reverse,
        )
        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "deadline": iso(t.deadline),
                    "tags": str_list(t.tags),
                    "estimated_duration": t.estimated_duration,
                    "is_archived": t.is_archived,
                }
                for t in result.tasks
            ],
            "total": result.filtered_count,
        }

    @mcp.tool()
    def get_task(task_id: int) -> dict[str, Any]:
        """Get detailed information about a specific task.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            Task details including notes
        """
        result = client.get_task_by_id(task_id)
        task = result.task
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority,
            "deadline": iso(task.deadline),
            "planned_start": iso(task.planned_start),
            "planned_end": iso(task.planned_end),
            "estimated_duration": task.estimated_duration,
            "actual_duration_hours": task.actual_duration_hours,
            "tags": str_list(task.tags),
            "depends_on": str_list(task.depends_on),
            "is_fixed": task.is_fixed,
            "is_archived": task.is_archived,
            "notes": result.notes_content,
        }

    @mcp.tool()
    def create_task(
        name: str,
        priority: int | None = None,
        deadline: str | None = None,
        estimated_duration: float | None = None,
        tags: list[str] | None = None,
        is_fixed: bool = False,
        planned_start: str | None = None,
        planned_end: str | None = None,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            name: Task name (required)
            priority: Task priority (higher = more important, default from config)
            deadline: Deadline in ISO format with time (e.g., '2025-12-11T18:00:00')
            estimated_duration: Estimated duration in hours (e.g., 0.5 = 30min, 1.5 = 1h30m)
            tags: List of tags for categorization
            is_fixed: Whether schedule is fixed (won't be moved by optimizer)
            planned_start: Planned start datetime in ISO format (e.g., '2025-12-11T09:00:00')
            planned_end: Planned end datetime in ISO format (e.g., '2025-12-11T17:00:00')

        Returns:
            Created task data with ID
        """
        deadline_dt = parse_iso_datetime(deadline, "deadline")
        planned_start_dt = parse_iso_datetime(planned_start, "planned_start")
        planned_end_dt = parse_iso_datetime(planned_end, "planned_end")

        result = client.create_task(
            name=name,
            priority=priority,
            deadline=deadline_dt,
            estimated_duration=estimated_duration,
            tags=tags,
            is_fixed=is_fixed,
            planned_start=planned_start_dt,
            planned_end=planned_end_dt,
        )
        return task_result(
            result,
            f"Task '{result.name}' created successfully",
            priority=result.priority,
        )

    @mcp.tool()
    def update_task(
        task_id: int,
        name: str | None = None,
        priority: int | None = None,
        deadline: str | None = None,
        estimated_duration: float | None = None,
        tags: list[str] | None = None,
        is_fixed: bool | None = None,
        planned_start: str | None = None,
        planned_end: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing task.

        Args:
            task_id: ID of the task to update
            name: New task name
            priority: New priority
            deadline: New deadline in ISO format with time (e.g., '2025-12-11T18:00:00')
            estimated_duration: New estimated duration in hours (e.g., 0.5 = 30min, 1.5 = 1h30m)
            tags: New tags list (replaces existing)
            is_fixed: New fixed status
            planned_start: New planned start datetime in ISO format (e.g., '2025-12-11T09:00:00')
            planned_end: New planned end datetime in ISO format (e.g., '2025-12-11T17:00:00')

        Returns:
            Updated task data
        """
        deadline_dt = parse_iso_datetime(deadline, "deadline")
        planned_start_dt = parse_iso_datetime(planned_start, "planned_start")
        planned_end_dt = parse_iso_datetime(planned_end, "planned_end")

        result = client.update_task(
            task_id=task_id,
            name=name,
            priority=priority,
            deadline=deadline_dt,
            estimated_duration=estimated_duration,
            tags=tags,
            is_fixed=is_fixed,
            planned_start=planned_start_dt,
            planned_end=planned_end_dt,
        )
        # TaskUpdateOutput has .task (TaskOperationOutput) and .updated_fields
        task = result.task
        return task_result(
            task,
            f"Task '{task.name}' updated successfully",
            priority=task.priority,
        )

    @mcp.tool()
    def delete_task(task_id: int, hard: bool = False) -> dict[str, Any]:
        """Delete a task.

        Args:
            task_id: ID of the task to delete
            hard: If True, permanently delete. If False, archive (soft delete).

        Returns:
            Confirmation message
        """
        if hard:
            client.remove_task(task_id)
            return {"message": f"Task {task_id} permanently deleted"}
        result = client.archive_task(task_id)
        return {
            "id": result.id,
            "message": f"Task '{result.name}' archived",
        }

    @mcp.tool()
    def restore_task(task_id: int) -> dict[str, Any]:
        """Restore an archived task.

        Args:
            task_id: ID of the task to restore

        Returns:
            Restored task data
        """
        result = client.restore_task(task_id)
        return task_result(result, f"Task '{result.name}' restored")
