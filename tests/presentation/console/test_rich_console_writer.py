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

    def test_print_task_start_time_new_start(self):
        """Test print_task_start_time for newly started task."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start="2025-10-16 10:00:00",
        )
        self.writer.print_task_start_time(task, was_already_in_progress=False)
        output = self.string_io.getvalue()
        self.assertIn("Started at:", output)
        self.assertIn("2025-10-16 10:00:00", output)

    def test_print_task_start_time_already_in_progress(self):
        """Test print_task_start_time for already in-progress task."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start="2025-10-16 09:00:00",
        )
        self.writer.print_task_start_time(task, was_already_in_progress=True)
        output = self.string_io.getvalue()
        self.assertIn("already IN_PROGRESS", output)
        self.assertIn("2025-10-16 09:00:00", output)

    def test_print_cannot_start_finished_task_error(self):
        """Test print_cannot_start_finished_task_error."""
        self.writer.print_cannot_start_finished_task_error(5, "COMPLETED")
        output = self.string_io.getvalue()
        self.assertIn("Cannot start task 5", output)
        self.assertIn("already COMPLETED", output)
        self.assertIn("cannot be restarted", output)

    def test_print_task_completion_time(self):
        """Test print_task_completion_time."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_end="2025-10-16 18:00:00",
        )
        self.writer.print_task_completion_time(task)
        output = self.string_io.getvalue()
        self.assertIn("Completed at:", output)
        self.assertIn("2025-10-16 18:00:00", output)

    def test_print_task_duration(self):
        """Test print_task_duration."""
        task = Task(
            id=1,
            name="Test",
            priority=100,
            actual_start="2025-10-16 10:00:00",
            actual_end="2025-10-16 14:30:00",
        )
        self.writer.print_task_duration(task)
        output = self.string_io.getvalue()
        self.assertIn("Duration:", output)
        self.assertIn("4.5h", output)

    def test_print_duration_comparison_over(self):
        """Test print_duration_comparison when actual > estimated."""
        self.writer.print_duration_comparison(5.0, 3.0)
        output = self.string_io.getvalue()
        self.assertIn("2.0h longer", output)

    def test_print_duration_comparison_under(self):
        """Test print_duration_comparison when actual < estimated."""
        self.writer.print_duration_comparison(3.0, 5.0)
        output = self.string_io.getvalue()
        self.assertIn("2.0h faster", output)

    def test_print_duration_comparison_exact(self):
        """Test print_duration_comparison when actual == estimated."""
        self.writer.print_duration_comparison(4.0, 4.0)
        output = self.string_io.getvalue()
        self.assertIn("exactly on estimate", output)

    def test_print_cannot_complete_finished_task_error(self):
        """Test print_cannot_complete_finished_task_error."""
        self.writer.print_cannot_complete_finished_task_error(10, "COMPLETED")
        output = self.string_io.getvalue()
        self.assertIn("Cannot complete task 10", output)
        self.assertIn("already COMPLETED", output)

    def test_print_cannot_complete_pending_task_error(self):
        """Test print_cannot_complete_pending_task_error."""
        self.writer.print_cannot_complete_pending_task_error(7)
        output = self.string_io.getvalue()
        self.assertIn("Cannot complete task 7", output)
        self.assertIn("still PENDING", output)
        self.assertIn("taskdog start 7", output)

    def test_print_schedule_updated(self):
        """Test print_schedule_updated."""
        task = Task(id=1, name="Test Task", priority=100)
        self.writer.print_schedule_updated(task, "2025-10-16 09:00:00", "2025-10-20 18:00:00")
        output = self.string_io.getvalue()
        self.assertIn("Set schedule for", output)
        self.assertIn("Test Task", output)
        self.assertIn("Start:", output)
        self.assertIn("End:", output)

    def test_print_no_fields_to_update_warning(self):
        """Test print_no_fields_to_update_warning."""
        self.writer.print_no_fields_to_update_warning()
        output = self.string_io.getvalue()
        self.assertIn("No fields to update", output)

    def test_print_task_fields_updated(self):
        """Test print_task_fields_updated."""
        task = Task(
            id=1,
            name="Test Task",
            priority=200,
            estimated_duration=3.5,
        )
        self.writer.print_task_fields_updated(task, ["priority", "estimated_duration"])
        output = self.string_io.getvalue()
        self.assertIn("Updated task", output)
        self.assertIn("Test Task", output)
        self.assertIn("priority:", output)
        self.assertIn("200", output)
        self.assertIn("estimated_duration:", output)
        self.assertIn("3.5h", output)

    def test_print_notes_file_created(self):
        """Test print_notes_file_created."""
        from pathlib import Path

        notes_path = Path("/tmp/notes/1.md")
        self.writer.print_notes_file_created(notes_path)
        output = self.string_io.getvalue()
        self.assertIn("Created notes file:", output)
        self.assertIn("/tmp/notes/1.md", output)

    def test_print_opening_editor(self):
        """Test print_opening_editor."""
        self.writer.print_opening_editor("vim")
        output = self.string_io.getvalue()
        self.assertIn("Opening vim", output)

    def test_print_notes_saved(self):
        """Test print_notes_saved."""
        self.writer.print_notes_saved(5)
        output = self.string_io.getvalue()
        self.assertIn("Notes saved for task #5", output)

    def test_print_task_removed(self):
        """Test print_task_removed."""
        self.writer.print_task_removed(10)
        output = self.string_io.getvalue()
        self.assertIn("Removed task with ID: 10", output)

    def test_print_task_archived(self):
        """Test print_task_archived."""
        self.writer.print_task_archived(15)
        output = self.string_io.getvalue()
        self.assertIn("Archived task with ID: 15", output)

    def test_print_optimization_result_dry_run(self):
        """Test print_optimization_result with dry run."""
        self.writer.print_optimization_result(5, is_dry_run=True)
        output = self.string_io.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("5 task(s)", output)

    def test_print_optimization_result_actual(self):
        """Test print_optimization_result without dry run."""
        self.writer.print_optimization_result(5, is_dry_run=False)
        output = self.string_io.getvalue()
        self.assertIn("Optimized schedules for 5 task(s)", output)

    def test_print_optimization_heading(self):
        """Test print_optimization_heading."""
        self.writer.print_optimization_heading()
        output = self.string_io.getvalue()
        self.assertIn("Configuration:", output)

    def test_print_export_success(self):
        """Test print_export_success."""
        self.writer.print_export_success(20, "/tmp/tasks.json")
        output = self.string_io.getvalue()
        self.assertIn("Exported 20 tasks", output)
        self.assertIn("/tmp/tasks.json", output)


if __name__ == "__main__":
    unittest.main()
