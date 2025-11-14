"""Tests for QueryClient."""

import unittest
from datetime import date
from unittest.mock import Mock, patch

from taskdog.infrastructure.api.query_client import QueryClient


class TestQueryClient(unittest.TestCase):
    """Test cases for QueryClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.notes_cache = {}
        self.client = QueryClient(self.mock_base, self.notes_cache)

    @patch("taskdog.infrastructure.api.query_client.convert_to_task_list_output")
    def test_list_tasks(self, mock_convert):
        """Test list_tasks makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "tasks": [],
            "total_count": 0,
            "filtered_count": 0,
        }
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.list_tasks(
            all=False,
            status="pending",
            tags=["urgent"],
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            sort_by="deadline",
            reverse=True,
        )

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "get")
        self.assertEqual(call_args[0][1], "/api/v1/tasks")

        params = call_args[1]["params"]
        self.assertEqual(params["all"], "false")
        self.assertEqual(params["status"], "pending")
        self.assertEqual(params["tags"], ["urgent"])
        self.assertEqual(params["start_date"], "2025-01-01")
        self.assertEqual(params["end_date"], "2025-01-31")
        self.assertEqual(params["sort"], "deadline")
        self.assertEqual(params["reverse"], "true")

        self.assertEqual(result, mock_output)
        mock_convert.assert_called_once_with(mock_response.json(), self.notes_cache)

    @patch("taskdog.infrastructure.api.query_client.convert_to_get_task_by_id_output")
    def test_get_task_by_id(self, mock_convert):
        """Test get_task_by_id makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_task_by_id(task_id=1)

        self.mock_base._safe_request.assert_called_once_with("get", "/api/v1/tasks/1")
        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.query_client.convert_to_get_task_detail_output")
    def test_get_task_detail(self, mock_convert):
        """Test get_task_detail makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": 1, "notes": "Content"}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_task_detail(task_id=1)

        self.mock_base._safe_request.assert_called_once_with("get", "/api/v1/tasks/1")
        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.query_client.convert_to_gantt_output")
    def test_get_gantt_data(self, mock_convert):
        """Test get_gantt_data makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"date_range": {}, "tasks": []}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_gantt_data(
            all=False,
            status="in_progress",
            sort_by="deadline",
            reverse=False,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "get")
        self.assertEqual(call_args[0][1], "/api/v1/gantt")

        params = call_args[1]["params"]
        self.assertEqual(params["all"], "false")
        self.assertEqual(params["status"], "in_progress")
        self.assertEqual(params["sort"], "deadline")
        self.assertEqual(params["reverse"], "false")
        self.assertEqual(params["start_date"], "2025-01-01")
        self.assertEqual(params["end_date"], "2025-01-31")

        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.query_client.convert_to_tag_statistics_output")
    def test_get_tag_statistics(self, mock_convert):
        """Test get_tag_statistics makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"tags": [], "total_tags": 0}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_tag_statistics()

        self.mock_base._safe_request.assert_called_once_with(
            "get", "/api/v1/tags/statistics"
        )
        self.assertEqual(result, mock_output)


if __name__ == "__main__":
    unittest.main()
