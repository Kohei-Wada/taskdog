"""Tests for RelationshipClient."""

from unittest.mock import Mock, patch

import pytest
from taskdog_client.relationship_client import RelationshipClient


class TestRelationshipClient:
    """Test cases for RelationshipClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = RelationshipClient(self.mock_base)

    @pytest.mark.parametrize(
        "method_name,method_kwargs,expected_http_method,expected_endpoint,expected_json",
        [
            (
                "add_dependency",
                {"depends_on_id": 2},
                "post",
                "/api/v1/tasks/1/dependencies",
                {"depends_on_id": 2},
            ),
            (
                "set_task_tags",
                {"tags": ["urgent", "backend"]},
                "put",
                "/api/v1/tasks/1/tags",
                {"tags": ["urgent", "backend"]},
            ),
        ],
        ids=["add_dependency", "set_task_tags"],
    )
    @patch("taskdog_client.relationship_client.convert_to_task_operation_output")
    def test_relationship_operation_with_payload(
        self,
        mock_convert,
        method_name,
        method_kwargs,
        expected_http_method,
        expected_endpoint,
        expected_json,
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
        assert call_args[0][0] == expected_http_method
        assert call_args[0][1] == expected_endpoint
        assert call_args[1]["json"] == expected_json
        assert result == mock_output

    @patch("taskdog_client.relationship_client.convert_to_task_operation_output")
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
        assert result == mock_output
