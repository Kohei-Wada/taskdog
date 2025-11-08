"""Unit tests for GanttCellFormatter."""

import unittest
from datetime import date, datetime

from rich.text import Text

from taskdog.constants.symbols import (
    SYMBOL_CANCELED,
    SYMBOL_EMPTY,
    SYMBOL_IN_PROGRESS,
    SYMBOL_TODAY,
)
from taskdog.renderers.gantt_cell_formatter import GanttCellFormatter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestGanttCellFormatter(unittest.TestCase):
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

        self.assertEqual(result["planned_start"], date(2025, 10, 1))
        self.assertEqual(result["planned_end"], date(2025, 10, 5))
        self.assertEqual(result["deadline"], date(2025, 10, 10))
        self.assertEqual(result["actual_start"], date(2025, 10, 1))
        self.assertIsNone(result["actual_end"])

    def test_parse_task_dates_with_no_dates(self):
        """Test parsing task dates when no dates are present."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        result = GanttCellFormatter.parse_task_dates(task)

        self.assertIsNone(result["planned_start"])
        self.assertIsNone(result["planned_end"])
        self.assertIsNone(result["deadline"])
        self.assertIsNone(result["actual_start"])
        self.assertIsNone(result["actual_end"])

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

        self.assertEqual(display, f" {SYMBOL_IN_PROGRESS} ")
        self.assertIn("bold blue", style)  # IN_PROGRESS color

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

        self.assertEqual(display, " 4 ")
        self.assertIn("on rgb", style)  # Has background color

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

        self.assertEqual(display, SYMBOL_EMPTY)
        self.assertEqual(style, "dim")

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

        self.assertEqual(display, SYMBOL_EMPTY)
        # Should have deadline background color (orange)
        self.assertIn("on rgb(200,100,0)", style)

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
        self.assertEqual(display, SYMBOL_EMPTY)

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
        self.assertEqual(display, SYMBOL_EMPTY)

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

        self.assertEqual(display, f" {SYMBOL_CANCELED} ")
        self.assertIn("bold red", style)  # CANCELED color

        # Test on different date - should not show the mark
        display, _style = GanttCellFormatter.format_timeline_cell(
            current_date=date(2025, 10, 2),
            hours=4.0,
            parsed_dates=parsed_dates,
            status=TaskStatus.CANCELED,
            holidays=set(),
        )

        self.assertEqual(display, SYMBOL_EMPTY)  # Not showing hours for CANCELED

    def test_build_date_header_lines(self):
        """Test building date header lines."""
        start_date = date(2025, 10, 1)
        end_date = date(2025, 10, 5)

        month_line, today_line, day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, set()
        )

        # Check that all are Text objects
        self.assertIsInstance(month_line, Text)
        self.assertIsInstance(today_line, Text)
        self.assertIsInstance(day_line, Text)

        # Check month line contains "Oct"
        self.assertIn("Oct", month_line.plain)

        # Check day line contains days 1-5
        day_text = day_line.plain
        self.assertIn("1", day_text)
        self.assertIn("2", day_text)
        self.assertIn("3", day_text)
        self.assertIn("4", day_text)
        self.assertIn("5", day_text)

    def test_build_date_header_lines_includes_today_marker(self):
        """Test that today's date gets a marker in the header."""
        today = date.today()
        start_date = today
        end_date = today

        _month_line, today_line, _day_line = GanttCellFormatter.build_date_header_lines(
            start_date, end_date, set()
        )

        # Today line should contain the today marker symbol
        self.assertIn(SYMBOL_TODAY, today_line.plain)

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

        self.assertIsInstance(result, Text)

        # Check that hours are ceiled correctly (6.5 -> 7, 8.5 -> 9)
        result_text = result.plain
        self.assertIn("4", result_text)  # 4.0 -> 4
        self.assertIn("7", result_text)  # 6.5 -> 7 (ceil)
        self.assertIn("9", result_text)  # 8.5 -> 9 (ceil)
        self.assertIn("0", result_text)  # 0.0 -> 0

    def test_build_legend(self):
        """Test building legend."""
        legend = GanttCellFormatter.build_legend()

        self.assertIsInstance(legend, Text)

        # Check that legend contains key terms
        legend_text = legend.plain
        self.assertIn("Legend:", legend_text)
        self.assertIn("Planned", legend_text)
        self.assertIn("IN_PROGRESS", legend_text)
        self.assertIn("COMPLETED", legend_text)
        self.assertIn("CANCELED", legend_text)
        self.assertIn("Deadline", legend_text)
        self.assertIn("Today", legend_text)
        self.assertIn("Saturday", legend_text)
        self.assertIn("Sunday", legend_text)

    def test_get_status_color(self):
        """Test getting status color."""
        # Test known statuses (using actual STATUS_COLORS_BOLD values)
        self.assertEqual(
            GanttCellFormatter.get_status_color(TaskStatus.PENDING), "yellow"
        )
        self.assertEqual(
            GanttCellFormatter.get_status_color(TaskStatus.IN_PROGRESS), "bold blue"
        )
        self.assertEqual(
            GanttCellFormatter.get_status_color(TaskStatus.COMPLETED), "bold green"
        )
        self.assertEqual(
            GanttCellFormatter.get_status_color(TaskStatus.CANCELED), "bold red"
        )

        # Test unknown status (should return default)
        self.assertEqual(GanttCellFormatter.get_status_color("UNKNOWN"), "white")


if __name__ == "__main__":
    unittest.main()
