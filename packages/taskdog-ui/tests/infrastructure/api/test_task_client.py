"""Tests for TaskClient."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from taskdog.infrastructure.api.task_client import TaskClient
from taskdog_core.domain.entities.task import TaskStatus


class TestTaskClient(unittest.TestCase):
    """Test cases for TaskClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = TaskClient(self.mock_base)

    @patch("taskdog.infrastructure.api.task_client.convert_to_task_operation_output")
    def test_create_task(self, mock_convert):
        """Test create_task makes correct API call."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "Test"}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.create_task(
            name="Test Task",
            priority=50,
            deadline=datetime(2025, 12, 31, 23, 59),
            estimated_duration=5.0,
            is_fixed=True,
            tags=["urgent"],
        )

        # Verify API call
        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "post")
        self.assertEqual(call_args[0][1], "/api/v1/tasks")

        payload = call_args[1]["json"]
        self.assertEqual(payload["name"], "Test Task")
        self.assertEqual(payload["priority"], 50)
        self.assertEqual(payload["estimated_duration"], 5.0)
        self.assertTrue(payload["is_fixed"])
        self.assertEqual(payload["tags"], ["urgent"])

        # Verify result
        self.assertEqual(result, mock_output)
        mock_convert.assert_called_once()

    @patch("taskdog.infrastructure.api.task_client.convert_to_task_operation_output")
    def test_create_task_error_handling(self, mock_convert):
        """Test create_task handles errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        self.mock_base._safe_request.return_value = mock_response

        self.client.create_task(name="Test")

        # Should call error handler
        self.mock_base._handle_error.assert_called_once_with(mock_response)

    def test_build_update_payload_all_fields(self):
        """Test _build_update_payload with all fields."""
        payload = self.client._build_update_payload(
            name="Updated",
            priority=75,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 17, 0),
            deadline=datetime(2025, 12, 31, 23, 59),
            estimated_duration=10.0,
            is_fixed=True,
            tags=["updated"],
        )

        self.assertEqual(payload["name"], "Updated")
        self.assertEqual(payload["priority"], 75)
        self.assertEqual(payload["status"], "IN_PROGRESS")
        self.assertEqual(payload["estimated_duration"], 10.0)
        self.assertTrue(payload["is_fixed"])
        self.assertEqual(payload["tags"], ["updated"])

    def test_build_update_payload_partial_fields(self):
        """Test _build_update_payload with only some fields."""
        payload = self.client._build_update_payload(
            name="Updated",
            priority=None,
            status=None,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
            is_fixed=None,
            tags=None,
        )

        self.assertEqual(payload, {"name": "Updated"})
        self.assertNotIn("priority", payload)
        self.assertNotIn("status", payload)

    @patch("taskdog.infrastructure.api.task_client.convert_to_update_task_output")
    def test_update_task(self, mock_convert):
        """Test update_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.update_task(
            task_id=1, name="Updated", priority=75, tags=["new"]
        )

        # Verify API call
        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "patch")
        self.assertEqual(call_args[0][1], "/api/v1/tasks/1")

        payload = call_args[1]["json"]
        self.assertEqual(payload["name"], "Updated")
        self.assertEqual(payload["priority"], 75)
        self.assertEqual(payload["tags"], ["new"])

        # Verify result
        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.task_client.convert_to_task_operation_output")
    def test_archive_task(self, mock_convert):
        """Test archive_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.archive_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/archive"
        )
        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.task_client.convert_to_task_operation_output")
    def test_restore_task(self, mock_convert):
        """Test restore_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.restore_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "post", "/api/v1/tasks/1/restore"
        )
        self.assertEqual(result, mock_output)

    def test_remove_task(self):
        """Test remove_task makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        self.mock_base._safe_request.return_value = mock_response

        self.client.remove_task(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "delete", "/api/v1/tasks/1"
        )

    def test_remove_task_not_found(self):
        """Test remove_task handles not found error."""
        mock_response = Mock()
        mock_response.is_success = False
        self.mock_base._safe_request.return_value = mock_response

        self.client.remove_task(task_id=999)

        self.mock_base._handle_error.assert_called_once_with(mock_response)


if __name__ == "__main__":
    unittest.main()
