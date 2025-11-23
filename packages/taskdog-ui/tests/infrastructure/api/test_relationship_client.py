"""Tests for RelationshipClient."""

import unittest
from unittest.mock import Mock, patch

from parameterized import parameterized

from taskdog.infrastructure.api.relationship_client import RelationshipClient


class TestRelationshipClient(unittest.TestCase):
    """Test cases for RelationshipClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = RelationshipClient(self.mock_base)

    @parameterized.expand(
        [
            (
                "add_dependency",
                "add_dependency",
                {"depends_on_id": 2},
                "post",
                "/api/v1/tasks/1/dependencies",
                {"depends_on_id": 2},
            ),
            (
                "set_task_tags",
                "set_task_tags",
                {"tags": ["urgent", "backend"]},
                "put",
                "/api/v1/tasks/1/tags",
                {"tags": ["urgent", "backend"]},
            ),
            (
                "log_hours",
                "log_hours",
                {"hours": 5.5, "date_str": "2025-01-15"},
                "post",
                "/api/v1/tasks/1/log-hours",
                {"hours": 5.5, "date": "2025-01-15"},
            ),
        ]
    )
    @patch(
        "taskdog.infrastructure.api.relationship_client.convert_to_task_operation_output"
    )
    def test_relationship_operation_with_payload(
        self,
        operation_name,
        method_name,
        method_kwargs,
        expected_http_method,
        expected_endpoint,
        expected_json,
        mock_convert,
    ):
        """Test relationship operations with JSON payload make correct API calls."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        method = getattr(self.client, method_name)
        result = method(task_id=1, **method_kwargs)

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], expected_http_method)
        self.assertEqual(call_args[0][1], expected_endpoint)
        self.assertEqual(call_args[1]["json"], expected_json)
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


if __name__ == "__main__":
    unittest.main()
