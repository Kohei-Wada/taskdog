"""Tests for RichConsoleWriter."""

import unittest
from datetime import datetime
from io import StringIO

from rich.console import Console

from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog_core.domain.entities.task import Task, TaskStatus


class RichConsoleWriterTest(unittest.TestCase):
    """Test cases for RichConsoleWriter."""

    def setUp(self):
        """Set up test fixtures."""
        self.string_io = StringIO()
        self.console = Console(file=self.string_io, force_terminal=True, width=80)
        self.writer = RichConsoleWriter(self.console)
        self.test_task = Task(
            id=1,
            name="Test Task",
            priority=100,
            status=TaskStatus.PENDING,
        )

    def test_success(self):
        """Test task_success method."""
        self.writer.task_success("Added", self.test_task)
        output = self.string_io.getvalue()
        self.assertIn("Added task", output)
        self.assertIn("Test Task", output)
        self.assertIn("ID:", output)
        self.assertIn("1", output)

    def test_error(self):
        """Test error method."""
        error = ValueError("Something went wrong")
        self.writer.error("testing", error)
        output = self.string_io.getvalue()
        self.assertIn("Error testing", output)
        self.assertIn("Something went wrong", output)

    def test_validation_error(self):
        """Test validation_error method."""
        self.writer.validation_error("Invalid input")
        output = self.string_io.getvalue()
        self.assertIn("Error: Invalid input", output)

    def test_warning(self):
        """Test warning method."""
        self.writer.warning("This is a warning")
        output = self.string_io.getvalue()
        self.assertIn("This is a warning", output)

    def test_info(self):
        """Test info method."""
        self.writer.info("This is information")
        output = self.string_io.getvalue()
        self.assertIn("This is information", output)

    def test_update_success(self):
        """Test update_success method."""
        self.writer.update_success(self.test_task, "priority", 3)
        output = self.string_io.getvalue()
        self.assertIn("Set priority for", output)
        self.assertIn("Test Task", output)
        self.assertIn("ID:", output)
        self.assertIn("1", output)
        self.assertIn("3", output)

    def test_update_success_with_formatter(self):
        """Test update_success with custom formatter."""
        self.writer.update_success(self.test_task, "duration", 2.5, lambda x: f"{x}h")
        output = self.string_io.getvalue()
        self.assertIn("Set duration for", output)
        self.assertIn("2", output)
        self.assertIn("5h", output)

    def test_print(self):
        """Test print method."""
        self.writer.print("Hello, World!")
        output = self.string_io.getvalue()
        self.assertIn("Hello, World!", output)

    def test_empty_line(self):
        """Test empty_line method."""
        self.writer.print("Line 1")
        self.writer.empty_line()
        self.writer.print("Line 2")
        output = self.string_io.getvalue()
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 3)  # 3 lines including empty line

    def test_get_width(self):
        """Test get_width method."""
        width = self.writer.get_width()
        self.assertEqual(width, 80)

    def test_task_start_time_new_start(self):
        """Test task_start_time for newly started task."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start=datetime(2025, 10, 16, 10, 0, 0),
        )
        self.writer.task_start_time(task, was_already_in_progress=False)
        output = self.string_io.getvalue()
        self.assertIn("Started at:", output)
        self.assertIn("2025", output)
        self.assertIn("10", output)
        self.assertIn("16", output)
        self.assertIn("10:00:00", output)

    def test_task_start_time_already_in_progress(self):
        """Test task_start_time for already in-progress task."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start=datetime(2025, 10, 16, 9, 0, 0),
        )
        self.writer.task_start_time(task, was_already_in_progress=True)
        output = self.string_io.getvalue()
        self.assertIn("already IN_PROGRESS", output)
        self.assertIn("2025", output)
        self.assertIn("10", output)
        self.assertIn("16", output)
        self.assertIn("09:00:00", output)

    def test_task_completion_details(self):
        """Test task_completion_details method."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start=datetime(2025, 10, 16, 10, 0, 0),
            actual_end=datetime(2025, 10, 16, 14, 30, 0),
            estimated_duration=4.0,
        )
        self.writer.task_completion_details(task)
        output = self.string_io.getvalue()
        self.assertIn("Completed at:", output)
        self.assertIn("2025", output)
        self.assertIn("10", output)
        self.assertIn("16", output)
        self.assertIn("14:30:00", output)
        self.assertIn("Duration:", output)
        self.assertIn("4", output)
        self.assertIn("5h", output)
        self.assertIn("0", output)
        self.assertIn("5h longer", output)

    def test_task_fields_updated(self):
        """Test task_fields_updated method."""
        task = Task(
            id=1,
            name="Test Task",
            priority=200,
            estimated_duration=3.5,
        )
        self.writer.task_fields_updated(task, ["priority", "estimated_duration"])
        output = self.string_io.getvalue()
        self.assertIn("Updated task", output)
        self.assertIn("Test Task", output)
        self.assertIn("priority:", output)
        self.assertIn("200", output)
        self.assertIn("estimated_duration:", output)
        self.assertIn("3", output)
        self.assertIn("5h", output)


if __name__ == "__main__":
    unittest.main()
