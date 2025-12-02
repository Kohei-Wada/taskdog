"""Tests for LifecycleClient."""

from unittest.mock import Mock, patch

import pytest

from taskdog.infrastructure.api.lifecycle_client import LifecycleClient


class TestLifecycleClient:
    """Test cases for LifecycleClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = LifecycleClient(self.mock_base)

    @pytest.mark.parametrize(
        "method_name,expected_endpoint",
        [
            ("start_task", "/api/v1/tasks/1/start"),
            ("complete_task", "/api/v1/tasks/1/complete"),
            ("pause_task", "/api/v1/tasks/1/pause"),
            ("cancel_task", "/api/v1/tasks/1/cancel"),
            ("reopen_task", "/api/v1/tasks/1/reopen"),
        ],
        ids=["start_task", "complete_task", "pause_task", "cancel_task", "reopen_task"],
    )
    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_lifecycle_operation_makes_correct_api_call(
        self, mock_convert, method_name, expected_endpoint
    ):
        """Test lifecycle operations make correct API calls."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        method = getattr(self.client, method_name)
        result = method(task_id=1)

        self.mock_base._safe_request.assert_called_once_with("post", expected_endpoint)
        assert result == mock_output

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_lifecycle_operation_error_handling(self, mock_convert):
        """Test lifecycle operations handle errors."""
        mock_response = Mock()
        mock_response.is_success = False
        self.mock_base._safe_request.return_value = mock_response

        self.client.start_task(task_id=999)

        self.mock_base._handle_error.assert_called_once_with(mock_response)
