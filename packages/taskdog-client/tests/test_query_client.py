"""Tests for QueryClient."""

from datetime import date
from unittest.mock import Mock, patch

import pytest
from taskdog_client.query_client import QueryClient


class TestQueryClient:
    """Test cases for QueryClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = QueryClient(self.mock_base)

    @patch("taskdog_client.query_client.convert_to_task_list_output")
    def test_list_tasks(self, mock_convert):
        """Test list_tasks makes correct API call."""
        mock_json = {
            "tasks": [],
            "total_count": 0,
            "filtered_count": 0,
        }
        self.mock_base._request_json.return_value = mock_json

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.list_tasks(
            include_archived=False,
            status="pending",
            tags=["urgent"],
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            sort_by="deadline",
            reverse=True,
        )

        self.mock_base._request_json.assert_called_once()
        call_args = self.mock_base._request_json.call_args
        assert call_args[0][0] == "get"
        assert call_args[0][1] == "/api/v1/tasks"

        params = call_args[1]["params"]
        assert params["all"] == "false"
        assert params["status"] == "pending"
        assert params["tags"] == ["urgent"]
        assert params["start_date"] == "2025-01-01"
        assert params["end_date"] == "2025-01-31"
        assert params["sort"] == "deadline"
        assert params["reverse"] == "true"

        assert result == mock_output
        mock_convert.assert_called_once_with(mock_json)

    @patch("taskdog_client.query_client.convert_to_task_list_output")
    def test_get_tasks_by_ids(self, mock_convert):
        """Test get_tasks_by_ids makes one batched API call with ids param."""
        mock_json = {"tasks": [], "total_count": 0, "filtered_count": 0}
        self.mock_base._request_json.return_value = mock_json
        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_tasks_by_ids([3, 1, 2])

        self.mock_base._request_json.assert_called_once_with(
            "get", "/api/v1/tasks/by-ids", params={"ids": [3, 1, 2]}
        )
        assert result == mock_output
        mock_convert.assert_called_once_with(mock_json)

    def test_get_tasks_by_ids_empty_skips_request(self):
        """Empty id list returns an empty result without an HTTP call."""
        result = self.client.get_tasks_by_ids([])

        self.mock_base._request_json.assert_not_called()
        assert result.tasks == []
        assert result.total_count == 0

    def test_get_task_by_id(self):
        """Test get_task_by_id makes correct API call."""
        with patch(
            "taskdog_client.query_client.convert_to_get_task_detail_output"
        ) as mock_convert:
            self.mock_base._request_json.return_value = {"id": 1, "notes": "Content"}

            mock_output = Mock()
            mock_convert.return_value = mock_output

            result = self.client.get_task_by_id(task_id=1)

            self.mock_base._request_json.assert_called_once_with(
                "get", "/api/v1/tasks/1"
            )
            assert result == mock_output

    @patch("taskdog_client.query_client.convert_to_task_list_output")
    def test_get_gantt_data(self, mock_convert):
        """Test get_gantt_data makes correct API call."""
        self.mock_base._request_json.return_value = {
            "tasks": [],
            "total_count": 0,
            "filtered_count": 0,
            "gantt": {"date_range": {}},
        }

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_gantt_data(
            include_archived=False,
            status="in_progress",
            sort_by="deadline",
            reverse=False,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        self.mock_base._request_json.assert_called_once()
        call_args = self.mock_base._request_json.call_args
        assert call_args[0][0] == "get"
        assert call_args[0][1] == "/api/v1/gantt"

        params = call_args[1]["params"]
        assert params["all"] == "false"
        assert params["status"] == "in_progress"
        assert params["sort"] == "deadline"
        assert params["reverse"] == "false"
        assert params["start_date"] == "2025-01-01"
        assert params["end_date"] == "2025-01-31"

        assert result == mock_output

    @patch("taskdog_client.query_client.convert_to_tag_statistics_output")
    def test_get_tag_statistics(self, mock_convert):
        """Test get_tag_statistics makes correct API call."""
        self.mock_base._request_json.return_value = {"tags": [], "total_tags": 0}

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.get_tag_statistics()

        self.mock_base._request_json.assert_called_once_with(
            "get", "/api/v1/tags/statistics"
        )
        assert result == mock_output
