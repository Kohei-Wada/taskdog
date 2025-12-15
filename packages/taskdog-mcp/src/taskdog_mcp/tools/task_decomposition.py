"""Task decomposition MCP tools.

Tools for breaking down large tasks into smaller subtasks.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient


def _build_subtask_tags(
    subtask_data: dict[str, Any],
    original_tags: list[str],
    group_tag: str | None,
) -> list[str]:
    """Build tags list for a subtask."""
    subtask_tags = list(subtask_data.get("tags", []))
    subtask_tags.extend(original_tags)
    if group_tag and group_tag not in subtask_tags:
        subtask_tags.append(group_tag)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(subtask_tags))


def _create_single_subtask(
    client: TaskdogApiClient,
    subtask_data: dict[str, Any],
    subtask_tags: list[str],
    subtask_priority: int,
) -> dict[str, Any]:
    """Create a single subtask and return its info."""
    result = client.create_task(
        name=subtask_data["name"],
        estimated_duration=subtask_data["estimated_duration"],
        priority=subtask_priority,
        tags=subtask_tags if subtask_tags else None,
    )
    # TaskOperationOutput is flat (id, name, status directly on result)
    return {
        "id": result.id,
        "name": result.name,
        "estimated_duration": subtask_data["estimated_duration"],
        "priority": subtask_priority,
        "tags": subtask_tags,
    }


def _update_decomposition_notes(
    client: TaskdogApiClient,
    task_id: int,
    created_subtasks: list[dict[str, Any]],
) -> None:
    """Update original task notes with decomposition info."""
    try:
        existing_notes, _ = client.get_task_notes(task_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note_addition = f"\n\n## Decomposition ({timestamp})\n"
        note_addition += f"Decomposed into {len(created_subtasks)} subtasks:\n"
        for st in created_subtasks:
            note_addition += (
                f"- [{st['id']}] {st['name']} ({st['estimated_duration']}h)\n"
            )

        new_notes = (existing_notes or "") + note_addition
        client.update_task_notes(task_id, new_notes)
    except Exception:
        pass  # Notes update is optional


def register_decomposition_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register decompose_task tool with the MCP server."""

    @mcp.tool()
    def decompose_task(
        task_id: int,
        subtasks: list[dict[str, Any]],
        group_tag: str | None = None,
        create_dependencies: bool = True,
        archive_original: bool = False,
    ) -> dict[str, Any]:
        """Decompose a large task into smaller subtasks.

        This tool helps break down complex tasks into manageable subtasks.
        Subtasks can be linked with sequential dependencies and grouped by tag.

        Note: Taskdog does not have parent-child relationships.
        Instead, use dependencies + tags + notes to express relationships.

        Args:
            task_id: ID of the original task to decompose
            subtasks: List of subtask definitions, each with:
                - name: Subtask name (required)
                - estimated_duration: Hours to complete (required)
                - priority: Priority level (optional, inherits from original)
                - tags: Additional tags (optional)
            group_tag: Tag to add to all subtasks for grouping (e.g., 'feature-x')
            create_dependencies: If True, create sequential dependencies
            archive_original: If True, archive the original task after decomposition

        Returns:
            Decomposition result with created subtask IDs
        """
        original = client.get_task_detail(task_id)
        # TaskDetailOutput has .task (TaskDetailDto)
        original_task = original.task
        original_tags = list(original_task.tags) if original_task.tags else []

        created_subtasks: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        previous_task_id: int | None = None

        for i, subtask_data in enumerate(subtasks):
            try:
                subtask_tags = _build_subtask_tags(
                    subtask_data, original_tags, group_tag
                )
                subtask_priority = (
                    subtask_data.get("priority") or original_task.priority
                )

                subtask_info = _create_single_subtask(
                    client, subtask_data, subtask_tags, subtask_priority
                )
                created_subtasks.append(subtask_info)

                if create_dependencies and previous_task_id is not None:
                    try:
                        client.add_dependency(subtask_info["id"], previous_task_id)
                    except Exception as dep_error:
                        errors.append(
                            {
                                "subtask_index": i,
                                "name": subtask_data["name"],
                                "error": f"Failed to create dependency: {dep_error}",
                            }
                        )

                previous_task_id = subtask_info["id"]

            except Exception as e:
                errors.append(
                    {
                        "subtask_index": i,
                        "name": subtask_data.get("name", f"subtask_{i}"),
                        "error": str(e),
                    }
                )

        if created_subtasks:
            _update_decomposition_notes(client, task_id, created_subtasks)

        if archive_original and created_subtasks:
            try:
                client.archive_task(task_id)
            except Exception as archive_error:
                errors.append(
                    {
                        "action": "archive_original",
                        "error": str(archive_error),
                    }
                )

        total_hours = sum(st["estimated_duration"] for st in created_subtasks)

        return {
            "original_task_id": task_id,
            "original_task_name": original_task.name,
            "created_subtasks": created_subtasks,
            "total_created": len(created_subtasks),
            "total_estimated_hours": total_hours,
            "group_tag": group_tag,
            "dependencies_created": create_dependencies and len(created_subtasks) > 1,
            "original_archived": archive_original and len(errors) == 0,
            "errors": errors if errors else None,
            "message": f"Decomposed '{original_task.name}' into {len(created_subtasks)} subtasks (total: {total_hours}h)",
        }


def register_relationship_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register relationship management tools with the MCP server."""

    @mcp.tool()
    def add_dependency(task_id: int, depends_on_id: int) -> dict[str, Any]:
        """Add a dependency between two tasks.

        The task will depend on the specified task (must be completed first).

        Args:
            task_id: ID of the task that will have the dependency
            depends_on_id: ID of the task it depends on

        Returns:
            Confirmation with updated task info
        """
        result = client.add_dependency(task_id, depends_on_id)
        # TaskOperationOutput is flat
        return {
            "id": result.id,
            "name": result.name,
            "depends_on": list(result.depends_on) if result.depends_on else [],
            "message": f"Task {task_id} now depends on task {depends_on_id}",
        }

    @mcp.tool()
    def remove_dependency(task_id: int, depends_on_id: int) -> dict[str, Any]:
        """Remove a dependency between two tasks.

        Args:
            task_id: ID of the task with the dependency
            depends_on_id: ID of the dependency to remove

        Returns:
            Confirmation with updated task info
        """
        result = client.remove_dependency(task_id, depends_on_id)
        return {
            "id": result.id,
            "name": result.name,
            "depends_on": list(result.depends_on) if result.depends_on else [],
            "message": f"Removed dependency: task {task_id} no longer depends on task {depends_on_id}",
        }

    @mcp.tool()
    def set_task_tags(task_id: int, tags: list[str]) -> dict[str, Any]:
        """Set tags for a task (replaces existing tags).

        Args:
            task_id: ID of the task
            tags: New list of tags

        Returns:
            Updated task info with new tags
        """
        result = client.set_task_tags(task_id, tags)
        return {
            "id": result.id,
            "name": result.name,
            "tags": list(result.tags) if result.tags else [],
            "message": f"Tags updated for task '{result.name}'",
        }


def register_notes_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register notes management tools with the MCP server."""

    @mcp.tool()
    def update_task_notes(task_id: int, content: str) -> dict[str, Any]:
        """Update notes for a task.

        Args:
            task_id: ID of the task
            content: New notes content (markdown)

        Returns:
            Confirmation message
        """
        client.update_task_notes(task_id, content)
        return {
            "id": task_id,
            "message": f"Notes updated for task {task_id}",
        }

    @mcp.tool()
    def get_task_notes(task_id: int) -> dict[str, Any]:
        """Get notes for a task.

        Args:
            task_id: ID of the task

        Returns:
            Task notes content
        """
        content, has_notes = client.get_task_notes(task_id)
        return {
            "id": task_id,
            "has_notes": has_notes,
            "content": content,
        }


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register all task decomposition and relationship tools.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """
    register_decomposition_tools(mcp, client)
    register_relationship_tools(mcp, client)
    register_notes_tools(mcp, client)
