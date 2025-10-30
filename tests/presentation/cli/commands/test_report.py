"""Tests for report command."""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.cli.commands.report import (
    _generate_markdown_report,
    _group_tasks_by_date,
    report_command,
)
from presentation.cli.context import CliContext
from presentation.console.rich_console_writer import RichConsoleWriter


class TestGroupTasksByDate(unittest.TestCase):
    """Tests for _group_tasks_by_date function."""

    def test_groups_tasks_by_allocation_date(self):
        """Test tasks are grouped by daily_allocations dates."""
        task1 = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 3.0, date(2025, 10, 31): 2.0},
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 4.0},
        )

        result = _group_tasks_by_date([task1, task2], None, None)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[date(2025, 10, 30)]), 2)  # task1 and task2
        self.assertEqual(len(result[date(2025, 10, 31)]), 1)  # task1 only
        self.assertEqual(result[date(2025, 10, 30)][0], (task1, 3.0))
        self.assertEqual(result[date(2025, 10, 30)][1], (task2, 4.0))

    def test_filters_by_start_date(self):
        """Test filtering by start_date."""
        task = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={
                date(2025, 10, 28): 2.0,
                date(2025, 10, 30): 3.0,
                date(2025, 10, 31): 2.0,
            },
        )

        result = _group_tasks_by_date([task], start_date=date(2025, 10, 30), end_date=None)

        self.assertEqual(len(result), 2)
        self.assertNotIn(date(2025, 10, 28), result)
        self.assertIn(date(2025, 10, 30), result)
        self.assertIn(date(2025, 10, 31), result)

    def test_filters_by_end_date(self):
        """Test filtering by end_date."""
        task = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={
                date(2025, 10, 30): 3.0,
                date(2025, 10, 31): 2.0,
                date(2025, 11, 1): 1.0,
            },
        )

        result = _group_tasks_by_date([task], start_date=None, end_date=date(2025, 10, 31))

        self.assertEqual(len(result), 2)
        self.assertIn(date(2025, 10, 30), result)
        self.assertIn(date(2025, 10, 31), result)
        self.assertNotIn(date(2025, 11, 1), result)

    def test_sorts_by_date(self):
        """Test result is sorted by date."""
        task = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={
                date(2025, 11, 1): 1.0,
                date(2025, 10, 30): 3.0,
                date(2025, 10, 31): 2.0,
            },
        )

        result = _group_tasks_by_date([task], None, None)

        dates = list(result.keys())
        self.assertEqual(dates, [date(2025, 10, 30), date(2025, 10, 31), date(2025, 11, 1)])

    def test_ignores_tasks_without_allocations(self):
        """Test tasks without daily_allocations are ignored."""
        task_with_allocation = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 3.0},
        )
        task_without_allocation = Task(
            id=2,
            name="Task 2",
            priority=5,
            status=TaskStatus.PENDING,
        )

        result = _group_tasks_by_date([task_with_allocation, task_without_allocation], None, None)

        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[date(2025, 10, 30)]), 1)


class TestGenerateMarkdownReport(unittest.TestCase):
    """Tests for _generate_markdown_report function."""

    def test_generates_correct_markdown_format(self):
        """Test markdown output format is correct."""
        task1 = Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING)
        task2 = Task(id=2, name="Task 2", priority=5, status=TaskStatus.PENDING)

        grouped_tasks = {
            date(2025, 10, 30): [(task1, 3.0), (task2, 4.0)],
            date(2025, 10, 31): [(task1, 2.0)],
        }

        result = _generate_markdown_report(grouped_tasks)

        expected = (
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
        )

        self.assertEqual(result, expected)

    def test_handles_zero_allocation(self):
        """Test tasks with zero allocation show '-'."""
        task = Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING)

        grouped_tasks = {
            date(2025, 10, 30): [(task, 0.0)],
        }

        result = _generate_markdown_report(grouped_tasks)

        self.assertIn("|Task 1|-|", result)
        self.assertIn("|sum|-|", result)

    def test_converts_float_hours_to_int(self):
        """Test allocated hours are converted to integers."""
        task = Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING)

        grouped_tasks = {
            date(2025, 10, 30): [(task, 3.7)],
        }

        result = _generate_markdown_report(grouped_tasks)

        self.assertIn("|Task 1|3|", result)
        self.assertIn("|sum|3|", result)


class TestReportCommand(unittest.TestCase):
    """Tests for report_command."""

    def setUp(self):
        """Set up test dependencies."""
        self.runner = CliRunner()
        self.repository = MagicMock(spec=JsonTaskRepository)
        self.console_writer = MagicMock(spec=RichConsoleWriter)
        self.cli_context = CliContext(
            console_writer=self.console_writer,
            repository=self.repository,
            time_tracker=MagicMock(),
            config=MagicMock(),
            notes_repository=MagicMock(),
        )

    @patch("presentation.cli.commands.report.TaskQueryService")
    def test_shows_warning_when_no_scheduled_tasks(self, mock_query_service_class):
        """Test warning is shown when no tasks have daily_allocations."""
        # Setup
        task_without_allocation = Task(id=1, name="Task 1", priority=5, status=TaskStatus.PENDING)

        mock_query_service = mock_query_service_class.return_value
        mock_query_service.get_filtered_tasks.return_value = [task_without_allocation]

        # Execute
        result = self.runner.invoke(report_command, [], obj=self.cli_context)

        # Verify
        self.assertEqual(result.exit_code, 0)
        self.console_writer.warning.assert_called_once()
        self.assertIn("No scheduled tasks found", self.console_writer.warning.call_args[0][0])

    @patch("presentation.cli.commands.report.TaskQueryService")
    def test_shows_warning_when_no_tasks_in_date_range(self, mock_query_service_class):
        """Test warning is shown when no tasks match the date range."""
        # Setup
        task = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 3.0},
        )

        mock_query_service = mock_query_service_class.return_value
        mock_query_service.get_filtered_tasks.return_value = [task]

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
            "No tasks found in the specified date range",
            self.console_writer.warning.call_args[0][0],
        )

    @patch("presentation.cli.commands.report.TaskQueryService")
    def test_generates_report_for_scheduled_tasks(self, mock_query_service_class):
        """Test report is generated for tasks with daily_allocations."""
        # Setup
        task1 = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 3.0},
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=5,
            status=TaskStatus.PENDING,
            daily_allocations={date(2025, 10, 30): 4.0},
        )

        mock_query_service = mock_query_service_class.return_value
        mock_query_service.get_filtered_tasks.return_value = [task1, task2]

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
