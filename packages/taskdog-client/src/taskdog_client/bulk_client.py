"""Bulk operations client for batch task processing."""

from typing import Any

from taskdog_client.base_client import BaseApiClient
from taskdog_client.converters import convert_to_task_operation_output
from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)


class BulkClient:
    """Client for bulk task operations.

    Sends multiple task IDs in a single request for batch processing.
    """

    def __init__(self, base_client: BaseApiClient):
        self._base = base_client

    def _bulk_operation(
        self, task_ids: list[int], operation: str
    ) -> BulkOperationOutput:
        """Execute a bulk operation.

        Args:
            task_ids: List of task IDs to operate on
            operation: Operation name (e.g., "start", "complete", "archive")

        Returns:
            BulkOperationOutput with per-task results
        """
        data = self._base._request_json(
            "post",
            f"/api/v1/tasks/bulk/{operation}",
            json={"task_ids": task_ids},
        )
        return self._parse_bulk_response(data)

    def _parse_bulk_response(self, data: dict[str, Any]) -> BulkOperationOutput:
        """Parse bulk operation response JSON into DTO."""
        if "results" not in data:
            raise ValueError("Invalid bulk operation response: missing 'results' key")
        results: list[BulkTaskResultOutput] = []
        for item in data["results"]:
            task = None
            if item.get("task") is not None:
                task = convert_to_task_operation_output(item["task"])
            results.append(
                BulkTaskResultOutput(
                    task_id=item["task_id"],
                    success=item["success"],
                    task=task,
                    error=item.get("error"),
                )
            )
        return BulkOperationOutput(results=results)

    def bulk_start(self, task_ids: list[int]) -> BulkOperationOutput:
        """Start multiple tasks."""
        return self._bulk_operation(task_ids, "start")

    def bulk_complete(self, task_ids: list[int]) -> BulkOperationOutput:
        """Complete multiple tasks."""
        return self._bulk_operation(task_ids, "complete")

    def bulk_pause(self, task_ids: list[int]) -> BulkOperationOutput:
        """Pause multiple tasks."""
        return self._bulk_operation(task_ids, "pause")

    def bulk_cancel(self, task_ids: list[int]) -> BulkOperationOutput:
        """Cancel multiple tasks."""
        return self._bulk_operation(task_ids, "cancel")

    def bulk_reopen(self, task_ids: list[int]) -> BulkOperationOutput:
        """Reopen multiple tasks."""
        return self._bulk_operation(task_ids, "reopen")

    def bulk_archive(self, task_ids: list[int]) -> BulkOperationOutput:
        """Archive multiple tasks."""
        return self._bulk_operation(task_ids, "archive")

    def bulk_restore(self, task_ids: list[int]) -> BulkOperationOutput:
        """Restore multiple tasks."""
        return self._bulk_operation(task_ids, "restore")

    def bulk_delete(self, task_ids: list[int]) -> BulkOperationOutput:
        """Delete multiple tasks permanently."""
        return self._bulk_operation(task_ids, "delete")
