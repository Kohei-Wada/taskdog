"""Tests for RelationshipClient."""

import unittest
from unittest.mock import Mock, patch

from taskdog.infrastructure.api.relationship_client import RelationshipClient


class TestRelationshipClient(unittest.TestCase):
    """Test cases for RelationshipClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = RelationshipClient(self.mock_base)

    @patch(
        "taskdog.infrastructure.api.relationship_client.convert_to_task_operation_output"
    )
    def test_add_dependency(self, mock_convert):
        """Test add_dependency makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.add_dependency(task_id=1, depends_on_id=2)

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "post")
        self.assertEqual(call_args[0][1], "/api/v1/tasks/1/dependencies")
        self.assertEqual(call_args[1]["json"], {"depends_on_id": 2})
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.relationship_client.convert_to_task_operation_output"
    )
    def test_remove_dependency(self, mock_convert):
        """Test remove_dependency makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.remove_dependency(task_id=1, depends_on_id=2)

        self.mock_base._safe_request.assert_called_once_with(
            "delete", "/api/v1/tasks/1/dependencies/2"
        )
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.relationship_client.convert_to_task_operation_output"
    )
    def test_set_task_tags(self, mock_convert):
        """Test set_task_tags makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.set_task_tags(task_id=1, tags=["urgent", "backend"])

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "put")
        self.assertEqual(call_args[0][1], "/api/v1/tasks/1/tags")
        self.assertEqual(call_args[1]["json"], {"tags": ["urgent", "backend"]})
        self.assertEqual(result, mock_output)

    @patch(
        "taskdog.infrastructure.api.relationship_client.convert_to_task_operation_output"
    )
    def test_log_hours(self, mock_convert):
        """Test log_hours makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.log_hours(task_id=1, hours=5.5, date_str="2025-01-15")

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "post")
        self.assertEqual(call_args[0][1], "/api/v1/tasks/1/log-hours")
        self.assertEqual(call_args[1]["json"], {"hours": 5.5, "date": "2025-01-15"})
        self.assertEqual(result, mock_output)


if __name__ == "__main__":
    unittest.main()
