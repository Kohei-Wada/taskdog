"""Task audit log MCP tools.

Tools for retrieving audit logs.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient


def register_tools(mcp: FastMCP, client: TaskdogApiClient) -> None:
    """Register audit log tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Taskdog API client
    """

    @mcp.tool()
    def list_audit_logs(
        task_id: int | None = None,
        operation: str | None = None,
        client_name: str | None = None,
        since: str | None = None,
        until: str | None = None,
        failed: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List audit logs with optional filtering.

        Args:
            task_id: Filter by task ID
            operation: Filter by operation type (e.g., 'create_task', 'complete_task')
            client_name: Filter by client name
            since: Filter logs after this datetime (ISO format, e.g., '2025-12-11T09:00:00')
            until: Filter logs before this datetime (ISO format, e.g., '2025-12-11T17:00:00')
            failed: If True, only show failed operations
            limit: Maximum number of logs to return

        Returns:
            Dictionary with logs list and metadata
        """
        start_date = datetime.fromisoformat(since) if since else None
        end_date = datetime.fromisoformat(until) if until else None
        success = False if failed else None

        result = client.list_audit_logs(
            client_filter=client_name,
            operation=operation,
            resource_id=task_id,
            success=success,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        logs = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "operation": log.operation,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "client_name": log.client_name,
                "success": log.success,
                "error_message": log.error_message,
            }
            for log in result.logs
        ]

        return {
            "logs": logs,
            "total_count": result.total_count,
            "message": f"Found {result.total_count} audit log(s)",
        }

    @mcp.tool()
    def get_audit_log(log_id: int) -> dict[str, Any]:
        """Get detailed information about a specific audit log entry.

        Args:
            log_id: The ID of the audit log entry to retrieve

        Returns:
            Detailed audit log entry including old and new values
        """
        log = client.get_audit_log(log_id)

        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "operation": log.operation,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "resource_name": log.resource_name,
            "client_name": log.client_name,
            "success": log.success,
            "error_message": log.error_message,
            "old_values": log.old_values,
            "new_values": log.new_values,
        }
