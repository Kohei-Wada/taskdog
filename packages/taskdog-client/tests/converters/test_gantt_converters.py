"""Tests for Gantt overlay converter functions."""

from datetime import date

from taskdog_client.converters.gantt_converters import (
    convert_to_gantt_overlay,
)


class TestConvertToGanttOverlay:
    """Test cases for convert_to_gantt_overlay."""

    def test_complete_data(self):
        """Test conversion with complete overlay data."""
        data = {
            "date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
            "task_daily_hours": {
                "1": {
                    "2025-01-05": 2.0,
                    "2025-01-06": 3.0,
                }
            },
            "daily_workload": {
                "2025-01-05": 2.0,
                "2025-01-06": 3.0,
            },
            "holidays": ["2025-01-01", "2025-01-13"],
            "total_estimated_duration": 5.0,
        }

        result = convert_to_gantt_overlay(data)

        assert result.date_range.start_date == date(2025, 1, 1)
        assert result.date_range.end_date == date(2025, 1, 31)
        assert result.task_daily_hours[1][date(2025, 1, 5)] == 2.0
        assert len(result.holidays) == 2
        assert date(2025, 1, 1) in result.holidays
        assert result.total_estimated_duration == 5.0

    def test_date_range_conversion(self):
        """Test that date_range dates are converted correctly."""
        data = {
            "date_range": {
                "start_date": "2025-06-01",
                "end_date": "2025-06-30",
            },
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_overlay(data)

        assert result.date_range.start_date == date(2025, 6, 1)
        assert result.date_range.end_date == date(2025, 6, 30)

    def test_task_daily_hours_conversion(self):
        """Test that task_daily_hours are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "task_daily_hours": {
                "1": {"2025-01-05": 2.0, "2025-01-06": 3.0},
                "2": {"2025-01-05": 1.0},
            },
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_overlay(data)

        assert len(result.task_daily_hours) == 2
        assert result.task_daily_hours[1][date(2025, 1, 5)] == 2.0
        assert result.task_daily_hours[1][date(2025, 1, 6)] == 3.0
        assert result.task_daily_hours[2][date(2025, 1, 5)] == 1.0

    def test_daily_workload_conversion(self):
        """Test that daily_workload is converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "task_daily_hours": {},
            "daily_workload": {
                "2025-01-05": 4.0,
                "2025-01-06": 6.0,
                "2025-01-07": 8.0,
            },
            "holidays": [],
        }

        result = convert_to_gantt_overlay(data)

        assert len(result.daily_workload) == 3
        assert result.daily_workload[date(2025, 1, 5)] == 4.0
        assert result.daily_workload[date(2025, 1, 6)] == 6.0
        assert result.daily_workload[date(2025, 1, 7)] == 8.0

    def test_holidays_conversion(self):
        """Test that holidays are converted correctly."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": ["2025-01-01", "2025-01-13", "2025-12-25"],
        }

        result = convert_to_gantt_overlay(data)

        assert len(result.holidays) == 3
        assert date(2025, 1, 1) in result.holidays
        assert date(2025, 1, 13) in result.holidays
        assert date(2025, 12, 25) in result.holidays

    def test_empty_holidays(self):
        """Test conversion with no holidays."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_overlay(data)

        assert len(result.holidays) == 0

    def test_default_total_estimated_duration(self):
        """Test that total_estimated_duration defaults to 0.0."""
        data = {
            "date_range": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "task_daily_hours": {},
            "daily_workload": {},
            "holidays": [],
        }

        result = convert_to_gantt_overlay(data)

        assert result.total_estimated_duration == 0.0
