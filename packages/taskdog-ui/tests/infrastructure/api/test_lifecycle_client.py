"""Tests for LifecycleClient."""

import unittest
from unittest.mock import Mock, patch

from taskdog.infrastructure.api.lifecycle_client import LifecycleClient


class TestLifecycleClient(unittest.TestCase):
    """Test cases for LifecycleClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = LifecycleClient(self.mock_base)

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_start_task(self, mock_convert):
        """Test start_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.start_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/start"
        )
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_complete_task(self, mock_convert):
        """Test complete_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.complete_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/complete"
        )
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_pause_task(self, mock_convert):
        """Test pause_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.pause_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/pause"
        )
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_cancel_task(self, mock_convert):
        """Test cancel_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.cancel_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/cancel"
        )
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.lifecycle_client.convert_to_task_operation_output"
    )
    def test_reopen_task(self, mock_convert):
        """Test reopen_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.reopen_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/reopen"
        )
        self.assertEqual(result, mock_output)

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


if __name__ == "__main__":
    unittest.main()
