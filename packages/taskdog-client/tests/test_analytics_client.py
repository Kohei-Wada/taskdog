"""Tests for AnalyticsClient."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from taskdog_client.analytics_client import AnalyticsClient


class TestAnalyticsClient:
    """Test cases for AnalyticsClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AnalyticsClient(self.mock_base)

    @patch("taskdog_client.analytics_client.convert_to_statistics_output")
    def test_calculate_statistics(self, mock_convert):
        """Test calculate_statistics makes correct API call."""
        self.mock_base._request_json.return_value = {"completion": {}}

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.calculate_statistics(period="7d")

        self.mock_base._request_json.assert_called_once_with(
            "get", "/api/v1/statistics?period=7d"
        )
        assert result == mock_output

    @patch("taskdog_client.analytics_client.convert_to_optimization_output")
    def test_optimize_schedule(self, mock_convert):
        """Test optimize_schedule makes correct API call."""
        self.mock_base._request_json.return_value = {"summary": {}}

        mock_output = Mock()
        mock_convert.return_value = mock_output

        start_date = datetime(2025, 1, 1, 0, 0)
        result = self.client.optimize_schedule(
            algorithm="greedy",
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=True,
        )

        self.mock_base._request_json.assert_called_once()
        call_args = self.mock_base._request_json.call_args
        assert call_args[0][0] == "post"
        assert call_args[0][1] == "/api/v1/optimize"

        payload = call_args[1]["json"]
        assert payload["algorithm"] == "greedy"
        assert payload["max_hours_per_day"] == 8.0
        assert payload["force_override"] is True
        assert result == mock_output

    def test_get_algorithm_metadata(self):
        """Test get_algorithm_metadata makes correct API call."""
        self.mock_base._request_json.return_value = [
            {
                "name": "greedy",
                "display_name": "Greedy",
                "description": "Fast algorithm",
            },
            {
                "name": "balanced",
                "display_name": "Balanced",
                "description": "Balanced approach",
            },
        ]

        result = self.client.get_algorithm_metadata()

        self.mock_base._request_json.assert_called_once_with(
            "get", "/api/v1/algorithms"
        )
        assert len(result) == 2
        assert result[0] == ("greedy", "Greedy", "Fast algorithm")
        assert result[1] == ("balanced", "Balanced", "Balanced approach")
