"""Tests for report command."""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from click.testing import CliRunner
from parameterized import parameterized

from taskdog.cli.commands.report import (
    _generate_markdown_report,
    _group_tasks_by_date,
    report_command,
)
from taskdog.cli.context import CliContext
from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog_core.application.dto.task_dto import GanttTaskDto
from taskdog_core.domain.entities.task import TaskStatus


def _create_gantt_task(
    task_id: int,
    name: str,
    status: TaskStatus = TaskStatus.PENDING,
    estimated_duration: float | None = None,
    planned_start: datetime | None = None,
    planned_end: datetime | None = None,
    is_finished: bool = False,
) -> GanttTaskDto:
    """Helper to create GanttTaskDto with sensible defaults."""
    return GanttTaskDto(
        id=task_id,
        name=name,
        status=status,
        estimated_duration=estimated_duration,
        planned_start=planned_start,
        planned_end=planned_end,
        actual_start=None,
        actual_end=None,
        deadline=None,
        is_finished=is_finished,
    )


class TestGroupTasksByDate(unittest.TestCase):
    """Tests for _group_tasks_by_date function."""

    def test_groups_tasks_by_allocation_date(self):
        """Test tasks are grouped by daily_allocations dates."""
        task1 = _create_gantt_task(1, "Task 1", estimated_duration=5.0)
        task2 = _create_gantt_task(2, "Task 2", estimated_duration=4.0)

        task_daily_hours = {
            1: {date(2025, 10, 30): 3.0, date(2025, 10, 31): 2.0},
            2: {date(2025, 10, 30): 4.0},
        }

        result = _group_tasks_by_date([task1, task2], task_daily_hours, None, None)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[date(2025, 10, 30)]), 2)  # task1 and task2
        self.assertEqual(len(result[date(2025, 10, 31)]), 1)  # task1 only
        self.assertEqual(result[date(2025, 10, 30)][0], (task1, 3.0))
        self.assertEqual(result[date(2025, 10, 30)][1], (task2, 4.0))

    @parameterized.expand(
        [
            (
                "start_date_filter",
                date(2025, 10, 30),  # start_date
                None,  # end_date
                {
                    date(2025, 10, 28): 2.0,
                    date(2025, 10, 30): 3.0,
                    date(2025, 10, 31): 2.0,
                },
                [date(2025, 10, 30), date(2025, 10, 31)],  # expected included
                [date(2025, 10, 28)],  # expected excluded
            ),
            (
                "end_date_filter",
                None,  # start_date
                date(2025, 10, 31),  # end_date
                {
                    date(2025, 10, 30): 3.0,
                    date(2025, 10, 31): 2.0,
                    date(2025, 11, 1): 1.0,
                },
                [date(2025, 10, 30), date(2025, 10, 31)],  # expected included
                [date(2025, 11, 1)],  # expected excluded
            ),
            (
                "both_filters",
                date(2025, 10, 30),  # start_date
                date(2025, 10, 31),  # end_date
                {
                    date(2025, 10, 28): 1.0,
                    date(2025, 10, 30): 3.0,
                    date(2025, 10, 31): 2.0,
                    date(2025, 11, 1): 1.0,
                },
                [date(2025, 10, 30), date(2025, 10, 31)],  # expected included
                [date(2025, 10, 28), date(2025, 11, 1)],  # expected excluded
            ),
        ]
    )
    def test_filters_by_date_range(
        self,
        name,
        start_date,
        end_date,
        daily_hours,
        expected_included,
        expected_excluded,
    ):
        """Test filtering by start_date and/or end_date."""
        task = _create_gantt_task(1, "Task 1", estimated_duration=7.0)
        task_daily_hours = {1: daily_hours}

        result = _group_tasks_by_date(
            [task], task_daily_hours, start_date=start_date, end_date=end_date
        )

        # Check expected dates are included
        for expected_date in expected_included:
            self.assertIn(
                expected_date, result, f"{name}: {expected_date} should be included"
            )

        # Check excluded dates are not present
        for excluded_date in expected_excluded:
            self.assertNotIn(
                excluded_date, result, f"{name}: {excluded_date} should be excluded"
            )

    def test_sorts_by_date(self):
        """Test result is sorted by date."""
        task = _create_gantt_task(1, "Task 1", estimated_duration=6.0)
        task_daily_hours = {
            1: {
                date(2025, 11, 1): 1.0,
                date(2025, 10, 30): 3.0,
                date(2025, 10, 31): 2.0,
            }
        }

        result = _group_tasks_by_date([task], task_daily_hours, None, None)

        dates = list(result.keys())
        self.assertEqual(
            dates, [date(2025, 10, 30), date(2025, 10, 31), date(2025, 11, 1)]
        )

    def test_ignores_tasks_without_schedule(self):
        """Test tasks without schedule (no task_daily_hours) are ignored."""
        task_with_allocation = _create_gantt_task(1, "Task 1", estimated_duration=3.0)
        task_without_schedule = _create_gantt_task(2, "Task 2", estimated_duration=4.0)

        task_daily_hours = {
            1: {date(2025, 10, 30): 3.0},
            # Task 2 has no daily hours
        }

        result = _group_tasks_by_date(
            [task_with_allocation, task_without_schedule],
            task_daily_hours,
            None,
            None,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[date(2025, 10, 30)]), 1)

    def test_includes_fixed_tasks_without_daily_allocations(self):
        """Test fixed tasks are included when they have task_daily_hours."""
        fixed_task = _create_gantt_task(
            1,
            "Fixed Task",
            estimated_duration=8.0,
            planned_start=datetime(2025, 10, 30, 9, 0),
            planned_end=datetime(2025, 10, 31, 18, 0),
        )
        optimized_task = _create_gantt_task(2, "Optimized Task", estimated_duration=3.0)

        task_daily_hours = {
            1: {date(2025, 10, 30): 4.0, date(2025, 10, 31): 4.0},
            2: {date(2025, 10, 30): 3.0},
        }

        result = _group_tasks_by_date(
            [fixed_task, optimized_task], task_daily_hours, None, None
        )

        # Both tasks should appear in the result
        self.assertIn(date(2025, 10, 30), result)

        # Check that both tasks are present on 2025/10/30
        tasks_on_oct_30 = [task for task, _ in result[date(2025, 10, 30)]]
        task_names = [task.name for task in tasks_on_oct_30]
        self.assertIn("Fixed Task", task_names)
        self.assertIn("Optimized Task", task_names)

    def test_includes_manually_scheduled_tasks(self):
        """Test manually scheduled tasks are included when they have task_daily_hours."""
        manual_task = _create_gantt_task(
            1,
            "Manual Task",
            estimated_duration=4.0,
            planned_start=datetime(2025, 10, 30, 9, 0),
            planned_end=datetime(2025, 10, 30, 18, 0),
        )

        task_daily_hours = {1: {date(2025, 10, 30): 4.0}}

        result = _group_tasks_by_date([manual_task], task_daily_hours, None, None)

        # Manual task should appear in the result
        self.assertIn(date(2025, 10, 30), result)
        self.assertEqual(len(result[date(2025, 10, 30)]), 1)
        self.assertEqual(result[date(2025, 10, 30)][0][0].name, "Manual Task")


class TestGenerateMarkdownReport(unittest.TestCase):
    """Tests for _generate_markdown_report function."""

    @parameterized.expand(
        [
            (
                "multiple_tasks_multiple_dates",
                {
                    date(2025, 10, 30): [
                        (_create_gantt_task(1, "Task 1"), 3.0),
                        (_create_gantt_task(2, "Task 2"), 4.0),
                    ],
                    date(2025, 10, 31): [(_create_gantt_task(1, "Task 1"), 2.0)],
                },
                (
                    "2025/10/30\n"
                    "|タスク|想定工数[h]|\n"
                    "|--|--|\n"
                    "|Task 1|3|\n"
                    "|Task 2|4|\n"
                    "|sum|7|\n"
                    "\n"
                    "2025/10/31\n"
                    "|タスク|想定工数[h]|\n"
                    "|--|--|\n"
                    "|Task 1|2|\n"
                    "|sum|2|\n"
                ),
            ),
            (
                "zero_allocation",
                {date(2025, 10, 30): [(_create_gantt_task(1, "Task 1"), 0.0)]},
                ("2025/10/30\n|タスク|想定工数[h]|\n|--|--|\n|Task 1|-|\n|sum|-|\n"),
            ),
            (
                "float_to_int_conversion",
                {date(2025, 10, 30): [(_create_gantt_task(1, "Task 1"), 3.7)]},
                ("2025/10/30\n|タスク|想定工数[h]|\n|--|--|\n|Task 1|3|\n|sum|3|\n"),
            ),
        ]
    )
    def test_markdown_generation(self, name, grouped_tasks, expected_output):
        """Test markdown generation with various scenarios."""
        result = _generate_markdown_report(grouped_tasks)
        self.assertEqual(result, expected_output)


class TestReportCommand(unittest.TestCase):
    """Tests for report_command."""

    def setUp(self):
        """Set up test dependencies."""
        self.runner = CliRunner()
        self.console_writer = MagicMock(spec=RichConsoleWriter)
        self.api_client = MagicMock()
        self.cli_context = CliContext(
            console_writer=self.console_writer,
            api_client=self.api_client,
            config=MagicMock(),
            holiday_checker=None,
        )

    def test_shows_warning_when_no_scheduled_tasks(self):
        """Test warning is shown when no tasks have task_daily_hours."""
        # Setup - empty gantt result
        mock_gantt_result = MagicMock()
        mock_gantt_result.tasks = []
        mock_gantt_result.task_daily_hours = {}
        self.api_client.get_gantt_data.return_value = mock_gantt_result

        # Execute
        result = self.runner.invoke(report_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called_once()
        self.assertIn(
            "No scheduled tasks found", self.console_writer.warning.call_args[0][0]
        )

    def test_shows_warning_when_no_tasks_in_date_range(self):
        """Test warning is shown when no tasks match the date range."""
        # Task has hours in October, but we query for November
        task = _create_gantt_task(1, "Task 1", estimated_duration=3.0)

        mock_gantt_result = MagicMock()
        mock_gantt_result.tasks = [task]
        mock_gantt_result.task_daily_hours = {1: {date(2025, 10, 30): 3.0}}
        self.api_client.get_gantt_data.return_value = mock_gantt_result

        # Execute - query for November dates (task is in October)
        result = self.runner.invoke(
            report_command,
            ["--start-date", "2025-11-01", "--end-date", "2025-11-30"],
            obj=self.cli_context,
        )

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called_once()
        self.assertIn(
            "No scheduled tasks found",
            self.console_writer.warning.call_args[0][0],
        )

    def test_generates_report_for_scheduled_tasks(self):
        """Test report is generated for tasks with task_daily_hours."""
        task1 = _create_gantt_task(1, "Task 1", estimated_duration=3.0)
        task2 = _create_gantt_task(2, "Task 2", estimated_duration=4.0)

        mock_gantt_result = MagicMock()
        mock_gantt_result.tasks = [task1, task2]
        mock_gantt_result.task_daily_hours = {
            1: {date(2025, 10, 30): 3.0},
            2: {date(2025, 10, 30): 4.0},
        }
        self.api_client.get_gantt_data.return_value = mock_gantt_result

        # Execute
        result = self.runner.invoke(report_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.print.assert_called_once()

        # Check the markdown output
        output = self.console_writer.print.call_args[0][0]
        self.assertIn("2025/10/30", output)
        self.assertIn("|タスク|想定工数[h]|", output)
        self.assertIn("|Task 1|3|", output)
        self.assertIn("|Task 2|4|", output)
        self.assertIn("|sum|7|", output)


if __name__ == "__main__":
    unittest.main()
