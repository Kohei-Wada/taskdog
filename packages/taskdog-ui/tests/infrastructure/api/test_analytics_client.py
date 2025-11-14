"""Tests for AnalyticsClient."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from taskdog.infrastructure.api.analytics_client import AnalyticsClient


class TestAnalyticsClient(unittest.TestCase):
    """Test cases for AnalyticsClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AnalyticsClient(self.mock_base)

    @patch("taskdog.infrastructure.api.analytics_client.convert_to_statistics_output")
    def test_calculate_statistics(self, mock_convert):
        """Test calculate_statistics makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"completion": {}}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        result = self.client.calculate_statistics(period="7d")

        self.mock_base._safe_request.assert_called_once_with(
            "get", "/api/v1/statistics?period=7d"
        )
        self.assertEqual(result, mock_output)

    @patch("taskdog.infrastructure.api.analytics_client.convert_to_optimization_output")
    def test_optimize_schedule(self, mock_convert):
        """Test optimize_schedule makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"summary": {}}
        self.mock_base._safe_request.return_value = mock_response

        mock_output = Mock()
        mock_convert.return_value = mock_output

        start_date = datetime(2025, 1, 1, 0, 0)
        result = self.client.optimize_schedule(
            algorithm="greedy",
            start_date=start_date,
            max_hours_per_day=8.0,
            force_override=True,
        )

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        self.assertEqual(call_args[0][0], "post")
        self.assertEqual(call_args[0][1], "/api/v1/optimize")

        payload = call_args[1]["json"]
        self.assertEqual(payload["algorithm"], "greedy")
        self.assertEqual(payload["max_hours_per_day"], 8.0)
        self.assertTrue(payload["force_override"])
        self.assertEqual(result, mock_output)

    def test_get_algorithm_metadata(self):
        """Test get_algorithm_metadata makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = [
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
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.get_algorithm_metadata()

        self.mock_base._safe_request.assert_called_once_with(
            "get", "/api/v1/algorithms"
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("greedy", "Greedy", "Fast algorithm"))
        self.assertEqual(result[1], ("balanced", "Balanced", "Balanced approach"))


if __name__ == "__main__":
    unittest.main()
