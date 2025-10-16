"""Tests for RichConsoleWriter."""

import unittest
from io import StringIO

from rich.console import Console

from domain.entities.task import Task, TaskStatus
from presentation.console.rich_console_writer import RichConsoleWriter


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

    def test_print_success(self):
        """Test print_success method."""
        self.writer.print_success("Added", self.test_task)
        output = self.string_io.getvalue()
        self.assertIn("Added task", output)
        self.assertIn("Test Task", output)
        self.assertIn("ID: 1", output)

    def test_print_error(self):
        """Test print_error method."""
        error = ValueError("Something went wrong")
        self.writer.print_error("testing", error)
        output = self.string_io.getvalue()
        self.assertIn("Error testing", output)
        self.assertIn("Something went wrong", output)

    def test_print_validation_error(self):
        """Test print_validation_error method."""
        self.writer.print_validation_error("Invalid input")
        output = self.string_io.getvalue()
        self.assertIn("Error: Invalid input", output)

    def test_print_warning(self):
        """Test print_warning method."""
        self.writer.print_warning("This is a warning")
        output = self.string_io.getvalue()
        self.assertIn("This is a warning", output)

    def test_print_info(self):
        """Test print_info method."""
        self.writer.print_info("This is information")
        output = self.string_io.getvalue()
        self.assertIn("This is information", output)

    def test_print_task_not_found_error(self):
        """Test print_task_not_found_error method."""
        self.writer.print_task_not_found_error(123)
        output = self.string_io.getvalue()
        self.assertIn("Task 123 not found", output)

    def test_print_task_not_found_error_parent(self):
        """Test print_task_not_found_error with parent flag."""
        self.writer.print_task_not_found_error(456, is_parent=True)
        output = self.string_io.getvalue()
        self.assertIn("Parent task 456 not found", output)

    def test_print_update_success(self):
        """Test print_update_success method."""
        self.writer.print_update_success(self.test_task, "priority", 3)
        output = self.string_io.getvalue()
        self.assertIn("Set priority for", output)
        self.assertIn("Test Task", output)
        self.assertIn("ID: 1", output)
        self.assertIn("3", output)

    def test_print_update_success_with_formatter(self):
        """Test print_update_success with custom formatter."""
        self.writer.print_update_success(
            self.test_task, "duration", 2.5, lambda x: f"{x}h"
        )
        output = self.string_io.getvalue()
        self.assertIn("Set duration for", output)
        self.assertIn("2.5h", output)

    def test_print(self):
        """Test print method."""
        self.writer.print("Hello, World!")
        output = self.string_io.getvalue()
        self.assertIn("Hello, World!", output)

    def test_print_empty_line(self):
        """Test print_empty_line method."""
        self.writer.print("Line 1")
        self.writer.print_empty_line()
        self.writer.print("Line 2")
        output = self.string_io.getvalue()
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 3)  # 3 lines including empty line

    def test_get_width(self):
        """Test get_width method."""
        width = self.writer.get_width()
        self.assertEqual(width, 80)


if __name__ == "__main__":
    unittest.main()
