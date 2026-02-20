"""Task tag MCP tools.

Tools for managing tags.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register tag management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def delete_tag(tag_name: str) -> dict[str, Any]:
        """Delete a tag from the system.

        Removes the tag and all its associations with tasks.

        Args:
            tag_name: Name of the tag to delete

        Returns:
            Confirmation with tag name and affected task count
        """
        result = client.delete_tag(tag_name)
        return {
            "tag_name": result.tag_name,
            "affected_task_count": result.affected_task_count,
            "message": f"Tag '{result.tag_name}' deleted (removed from {result.affected_task_count} tasks)",
        }
