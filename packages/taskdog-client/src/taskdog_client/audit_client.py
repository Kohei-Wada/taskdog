"""Audit log client."""

from datetime import datetime
from typing import Any

from taskdog_client.base_client import BaseApiClient
from taskdog_core.application.dto.audit_log_dto import (
    AuditLogListOutput,
    AuditLogOutput,
)


class AuditClient:
    """Client for audit log operations.

    Operations:
    - List audit logs with filtering
    - Get single audit log by ID
    """

    def __init__(self, base_client: BaseApiClient):
        """Initialize audit client.

        Args:
            base_client: Base API client for HTTP operations
        """
        self._base = base_client

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
        """List audit logs with optional filtering.

        Args:
            client_filter: Filter by client name
            operation: Filter by operation type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            success: Filter by success status
            start_date: Filter logs after this datetime
            end_date: Filter logs before this datetime
            limit: Maximum number of logs to return
            offset: Number of logs to skip for pagination

        Returns:
            AuditLogListOutput with logs and pagination info
        """
        params: dict[str, str | int] = {"limit": limit, "offset": offset}

        if client_filter is not None:
            params["client"] = client_filter
        if operation is not None:
            params["operation"] = operation
        if resource_type is not None:
            params["resource_type"] = resource_type
        if resource_id is not None:
            params["resource_id"] = resource_id
        if success is not None:
            params["success"] = str(success).lower()
        if start_date is not None:
            params["start_date"] = start_date.isoformat()
        if end_date is not None:
            params["end_date"] = end_date.isoformat()

        data = self._base._request_json("get", "/api/v1/audit-logs", params=params)
        return self._convert_to_list_output(data)

    def get_audit_log(self, log_id: int) -> AuditLogOutput | None:
        """Get a single audit log by ID.

        Args:
            log_id: Audit log ID

        Returns:
            AuditLogOutput if found, None otherwise
        """
        response = self._base._safe_request("get", f"/api/v1/audit-logs/{log_id}")
        if response.status_code == 404:
            return None
        if not response.is_success:
            self._base._handle_error(response)

        data = response.json()
        if data is None:
            return None
        return self._convert_to_output(data)

    def _convert_to_output(self, data: dict[str, Any]) -> AuditLogOutput:
        """Convert API response to AuditLogOutput DTO."""
        # Parse timestamp with error handling for malformed data
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
        except (ValueError, KeyError):
            # Fallback to current time if timestamp is invalid or missing
            timestamp = datetime.now()

        return AuditLogOutput(
            id=data["id"],
            timestamp=timestamp,
            client_name=data.get("client_name"),
            operation=data["operation"],
            resource_type=data["resource_type"],
            resource_id=data.get("resource_id"),
            resource_name=data.get("resource_name"),
            old_values=data.get("old_values"),
            new_values=data.get("new_values"),
            success=data["success"],
            error_message=data.get("error_message"),
        )

    def _convert_to_list_output(self, data: dict[str, Any]) -> AuditLogListOutput:
        """Convert API response to AuditLogListOutput DTO."""
        logs = [self._convert_to_output(log) for log in data["logs"]]
        return AuditLogListOutput(
            logs=logs,
            total_count=data["total_count"],
            limit=data["limit"],
            offset=data["offset"],
        )
