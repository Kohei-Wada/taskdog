"""Tests for BulkClient."""

from unittest.mock import Mock, patch

import pytest
from taskdog_client.bulk_client import BulkClient


class TestBulkClient:
    """Test cases for BulkClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = BulkClient(self.mock_base)

    def _make_bulk_response(self, results):
        """Helper to create a bulk response dict."""
        return {"results": results}

    def _make_success_result(self, task_id, status="IN_PROGRESS"):
        """Helper to create a successful result."""
        return {
            "task_id": task_id,
            "success": True,
            "task": {
                "id": task_id,
                "name": f"Task {task_id}",
                "status": status,
                "priority": 1,
                "deadline": None,
                "estimated_duration": None,
                "planned_start": None,
                "planned_end": None,
                "actual_start": None,
                "actual_end": None,
                "actual_duration": None,
                "actual_duration_hours": None,
                "depends_on": [],
                "tags": [],
                "is_fixed": False,
                "is_archived": False,
            },
            "error": None,
        }

    def _make_failure_result(self, task_id, error="Task not found"):
        """Helper to create a failed result."""
        return {
            "task_id": task_id,
            "success": False,
            "task": None,
            "error": error,
        }

    @pytest.mark.parametrize(
        "method_name,expected_operation",
        [
            ("bulk_start", "start"),
            ("bulk_complete", "complete"),
            ("bulk_pause", "pause"),
            ("bulk_cancel", "cancel"),
            ("bulk_reopen", "reopen"),
            ("bulk_archive", "archive"),
            ("bulk_restore", "restore"),
            ("bulk_delete", "delete"),
        ],
    )
    @patch("taskdog_client.bulk_client.convert_to_task_operation_output")
    def test_bulk_operation_makes_correct_api_call(
        self, mock_convert, method_name, expected_operation
    ):
        """Test bulk operations make correct API calls."""
        mock_convert.return_value = Mock()
        self.mock_base._request_json.return_value = self._make_bulk_response(
            [self._make_success_result(1)]
        )

        method = getattr(self.client, method_name)
        method(task_ids=[1, 2])

        self.mock_base._request_json.assert_called_once_with(
            "post",
            f"/api/v1/tasks/bulk/{expected_operation}",
            json={"task_ids": [1, 2]},
        )

    @patch("taskdog_client.bulk_client.convert_to_task_operation_output")
    def test_bulk_operation_parses_success_results(self, mock_convert):
        """Test parsing successful results from bulk operation."""
        mock_output = Mock()
        mock_convert.return_value = mock_output
        self.mock_base._request_json.return_value = self._make_bulk_response(
            [self._make_success_result(1), self._make_success_result(2)]
        )

        result = self.client.bulk_start(task_ids=[1, 2])

        assert len(result.results) == 2
        assert result.results[0].task_id == 1
        assert result.results[0].success is True
        assert result.results[0].task == mock_output
        assert result.results[0].error is None

    @patch("taskdog_client.bulk_client.convert_to_task_operation_output")
    def test_bulk_operation_parses_failure_results(self, mock_convert):
        """Test parsing failed results from bulk operation."""
        self.mock_base._request_json.return_value = self._make_bulk_response(
            [self._make_failure_result(99, "Task with ID 99 not found")]
        )

        result = self.client.bulk_start(task_ids=[99])

        assert len(result.results) == 1
        assert result.results[0].task_id == 99
        assert result.results[0].success is False
        assert result.results[0].task is None
        assert result.results[0].error == "Task with ID 99 not found"
        mock_convert.assert_not_called()

    @patch("taskdog_client.bulk_client.convert_to_task_operation_output")
    def test_bulk_operation_parses_mixed_results(self, mock_convert):
        """Test parsing mixed success/failure results."""
        mock_output = Mock()
        mock_convert.return_value = mock_output
        self.mock_base._request_json.return_value = self._make_bulk_response(
            [
                self._make_success_result(1),
                self._make_failure_result(99),
            ]
        )

        result = self.client.bulk_start(task_ids=[1, 99])

        assert len(result.results) == 2
        assert result.results[0].success is True
        assert result.results[0].task == mock_output
        assert result.results[1].success is False
        assert result.results[1].task is None

    def test_bulk_delete_success_has_no_task(self):
        """Test bulk delete returns null task on success."""
        self.mock_base._request_json.return_value = self._make_bulk_response(
            [
                {
                    "task_id": 1,
                    "success": True,
                    "task": None,
                    "error": None,
                }
            ]
        )

        result = self.client.bulk_delete(task_ids=[1])

        assert result.results[0].success is True
        assert result.results[0].task is None

    def test_bulk_operation_propagates_errors(self):
        """Test bulk operations propagate HTTP errors from _request_json."""
        from taskdog_core.domain.exceptions.task_exceptions import (
            ServerConnectionError,
        )

        self.mock_base._request_json.side_effect = ServerConnectionError(
            "http://localhost:8000", Exception("Connection refused")
        )

        with pytest.raises(ServerConnectionError):
            self.client.bulk_start(task_ids=[1])
