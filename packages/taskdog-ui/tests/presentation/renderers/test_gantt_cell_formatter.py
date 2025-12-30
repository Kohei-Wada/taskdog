"""Unit tests for GanttCellFormatter."""

from datetime import date, datetime

import pytest
from rich.text import Text

from taskdog.constants.symbols import (
    SYMBOL_CANCELED,
    SYMBOL_EMPTY,
    SYMBOL_IN_PROGRESS,
    SYMBOL_TODAY,
)
from taskdog.renderers.gantt_cell_formatter import GanttCellFormatter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestGanttCellFormatter:
    """Test cases for GanttCellFormatter."""

    def test_parse_task_dates_with_all_dates(self):
        """Test parsing task dates when all dates are present."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime(2025, 10, 1, 9, 0, 0),
            planned_end=datetime(2025, 10, 5, 18, 0, 0),
            deadline=datetime(2025, 10, 10, 18, 0, 0),
            actual_start=datetime(2025, 10, 1, 9, 0, 0),
            actual_end=None,
        )

        result = GanttCellFormatter.parse_task_dates(task)

        assert result["planned_start"] == date(2025, 10, 1)
        assert result["planned_end"] == date(2025, 10, 5)
        assert result["deadline"] == date(2025, 10, 10)
        assert result["actual_start"] == date(2025, 10, 1)
        assert result["actual_end"] is None

    def test_parse_task_dates_with_no_dates(self):
        """Test parsing task dates when no dates are present."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        result = GanttCellFormatter.parse_task_dates(task)

        assert result["planned_start"] is None
        assert result["planned_end"] is None
        assert result["deadline"] is None
        assert result["actual_start"] is None
        assert result["actual_end"] is None

    def test_format_timeline_cell_actual_period(self):
        """Test formatting a cell in the actual period."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": date(2025, 10, 1),
            "actual_end": date(2025, 10, 3),
            "deadline": None,
        }

        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 2),
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.IN_PROGRESS,
            holidays=set(),
        )

        assert display == f" {SYMBOL_IN_PROGRESS} "
        assert "bold blue" in style  # IN_PROGRESS color

    def test_format_timeline_cell_planned_period_with_hours(self):
        """Test formatting a cell in the planned period with allocated hours."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": None,
            "actual_end": None,
            "deadline": None,
        }

        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 2),
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        assert display == " 4 "
        assert "on rgb" in style  # Has background color

    def test_format_timeline_cell_empty(self):
        """Test formatting an empty cell (no hours, not in any period)."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": None,
            "actual_end": None,
            "deadline": None,
        }

        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 10),  # Outside planned period
            hours=0.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        assert display == SYMBOL_EMPTY
        assert style == "dim"

    def test_format_timeline_cell_deadline(self):
        """Test formatting a cell on the deadline date."""
        parsed_dates = {
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
            "deadline": date(2025, 10, 10),
        }

        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 10),
            hours=0.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        assert display == SYMBOL_EMPTY
        # Should have deadline background color (orange)
        assert "on rgb(200,100,0)" in style

    def test_format_timeline_cell_completed_hides_planned_hours(self):
        """Test that completed tasks don't show planned hours."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": date(2025, 10, 1),
            "actual_end": date(2025, 10, 3),
            "deadline": None,
        }

        display, _style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 4),  # After actual_end, in planned period
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.COMPLETED,
            holidays=set(),
        )

        # Should show empty symbol instead of hours for completed tasks
        assert display == SYMBOL_EMPTY

    def test_format_timeline_cell_canceled_hides_planned_hours(self):
        """Test that canceled tasks don't show planned hours."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": date(2025, 10, 1),
            "actual_end": date(2025, 10, 3),
            "deadline": None,
        }

        display, _style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 4),  # After actual_end, in planned period
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.CANCELED,
            holidays=set(),
        )

        # Should show empty symbol instead of hours for canceled tasks
        assert display == SYMBOL_EMPTY

    def test_format_timeline_cell_canceled_without_actual_start(self):
        """Test that canceled tasks without actual_start show mark on actual_end date."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": None,  # CANCELED without starting
            "actual_end": date(2025, 10, 3),
            "deadline": None,
        }

        # Test on actual_end date - should show the mark
        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 3),
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.CANCELED,
            holidays=set(),
        )

        assert display == f" {SYMBOL_CANCELED} "
        assert "bold red" in style  # CANCELED color

        # Test on different date - should not show the mark
        display, _style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 2),
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.CANCELED,
            holidays=set(),
        )

        assert display == SYMBOL_EMPTY  # Not showing hours for CANCELED

    def test_build_date_header_lines(self):
        """Test building date header lines."""
        start_date = date(2025, 10, 1)
        end_date = date(2025, 10, 5)

        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, set()
        )

        # Check that all are Text objects
        assert isinstance(month_line, Text)
        assert isinstance(today_line, Text)
        assert isinstance(day_line, Text)

        # Check month line contains "Oct"
        assert "Oct" in month_line.plain

        # Check day line contains days 1-5
        day_text = day_line.plain
        assert "1" in day_text
        assert "2" in day_text
        assert "3" in day_text
        assert "4" in day_text
        assert "5" in day_text

    def test_build_date_header_lines_includes_today_marker(self):
        """Test that today's date gets a marker in the header."""
        today = date.today()
        start_date = today
        end_date = today

        _month_line, today_line, _day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, set()
        )

        # Today line should contain the today marker symbol
        assert SYMBOL_TODAY in today_line.plain

    def test_build_workload_timeline(self):
        """Test building workload timeline."""
        daily_workload = {
            date(2025, 10, 1): 4.0,
            date(2025, 10, 2): 6.5,
            date(2025, 10, 3): 8.5,
            date(2025, 10, 4): 0.0,
        }
        start_date = date(2025, 10, 1)
        end_date = date(2025, 10, 4)

        result = GanttCellFormatter.build_workload_timeline(
            daily_workload, start_date, end_date
        )

        assert isinstance(result, Text)

        # Check that hours are ceiled correctly (6.5 -> 7, 8.5 -> 9)
        result_text = result.plain
        assert "4" in result_text  # 4.0 -> 4
        assert "7" in result_text  # 6.5 -> 7 (ceil)
        assert "9" in result_text  # 8.5 -> 9 (ceil)
        assert "0" in result_text  # 0.0 -> 0

    def test_build_legend(self):
        """Test building legend."""
        legend = GanttCellFormatter.build_legend()

        assert isinstance(legend, Text)

        # Check that legend contains key terms
        legend_text = legend.plain
        assert "Legend:" in legend_text
        assert "Planned" in legend_text
        assert "IN_PROGRESS" in legend_text
        assert "COMPLETED" in legend_text
        assert "CANCELED" in legend_text
        assert "Deadline" in legend_text
        assert "Today" in legend_text
        assert "Saturday" in legend_text
        assert "Sunday" in legend_text

    @pytest.mark.parametrize(
        "status,expected_color",
        [
            (TaskStatus.PENDING, "yellow"),
            (TaskStatus.IN_PROGRESS, "bold blue"),
            (TaskStatus.COMPLETED, "bold green"),
            (TaskStatus.CANCELED, "bold red"),
            ("UNKNOWN", "white"),
        ],
        ids=["pending", "in_progress", "completed", "canceled", "unknown"],
    )
    def test_get_status_color(self, status, expected_color):
        """Test getting status color."""
        assert GanttCellFormatter.get_status_color(status) == expected_color

    def test_format_timeline_cell_allocated_hours_outside_planned_period(self):
        """Test that cells with allocated hours outside planned period get correct background color.

        This test verifies the fix for the bug where cells with hours > 0
        but outside the planned period (is_planned == False) had no background color.
        """
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 3),  # Planned period ends on 10/3
            "actual_start": None,
            "actual_end": None,
            "deadline": None,
        }

        # Test a cell OUTSIDE the planned period but WITH allocated hours
        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 5),  # Outside planned period (10/1-10/3)
            hours=4.0,  # Has allocated hours
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        # Should show hours display
        assert display == " 4 "
        # Should have "Allocated hours" background color (not dim)
        assert "on rgb" in style
        assert "dim" not in style

    def test_format_timeline_cell_no_hours_outside_planned_period(self):
        """Test that cells without hours outside planned period are dim."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 3),
            "actual_start": None,
            "actual_end": None,
            "deadline": None,
        }

        # Test a cell OUTSIDE the planned period and WITHOUT allocated hours
        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 5),  # Outside planned period
            hours=0.0,  # No allocated hours
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        # Should show empty symbol and be dim
        assert display == SYMBOL_EMPTY
        assert style == "dim"

    def test_format_timeline_cell_planned_period_without_hours(self):
        """Test that cells in planned period without hours get light background."""
        parsed_dates = {
            "planned_start": date(2025, 10, 1),
            "planned_end": date(2025, 10, 5),
            "actual_start": None,
            "actual_end": None,
            "deadline": None,
        }

        # Test a cell INSIDE the planned period but WITHOUT allocated hours
        display, style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 3),  # Inside planned period
            hours=0.0,  # No allocated hours
            parsed_dates=parsed_dates,
            status=TaskStatus.PENDING,
            holidays=set(),
        )

        # Should show empty symbol but with planned period background
        assert display == SYMBOL_EMPTY
        assert "on rgb" in style  # Has light background color
