"""Tests for TUICommandBase."""

import unittest
from unittest.mock import MagicMock

from domain.entities.task import Task, TaskStatus
from presentation.tui.commands.base import TUICommandBase


class ConcreteCommand(TUICommandBase):
    """Concrete command for testing."""

    def execute(self) -> None:
        """Dummy execute implementation."""
        pass


class TestTUICommandBase(unittest.TestCase):
    """Test cases for TUICommandBase."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = MagicMock()
        self.app.repository = MagicMock()
        self.app.time_tracker = MagicMock()
        self.app.query_service = MagicMock()
        self.app.main_screen = MagicMock()
        self.command = ConcreteCommand(self.app)

    def test_initialization(self):
        """Test command initialization."""
        self.assertEqual(self.command.app, self.app)
        self.assertEqual(self.command.repository, self.app.repository)
        self.assertEqual(self.command.time_tracker, self.app.time_tracker)
        self.assertEqual(self.command.query_service, self.app.query_service)

    def test_get_selected_task_success(self):
        """Test getting selected task successfully."""
        expected_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)
        self.app.main_screen.task_table.get_selected_task.return_value = expected_task

        result = self.command.get_selected_task()

        self.assertEqual(result, expected_task)

    def test_get_selected_task_no_screen(self):
        """Test getting selected task when screen is not available."""
        self.app.main_screen = None

        result = self.command.get_selected_task()

        self.assertIsNone(result)

    def test_get_selected_task_no_table(self):
        """Test getting selected task when table is not available."""
        self.app.main_screen.task_table = None

        result = self.command.get_selected_task()

        self.assertIsNone(result)

    def test_reload_tasks(self):
        """Test reloading tasks."""
        self.command.reload_tasks()

        self.app._load_tasks.assert_called_once()

    def test_notify_success(self):
        """Test success notification."""
        message = "Operation successful"
        self.command.notify_success(message)

        self.app.notify.assert_called_once_with(message)

    def test_notify_error(self):
        """Test error notification."""
        message = "Operation failed"
        exception = Exception("Test error")

        self.command.notify_error(message, exception)

        self.app.notify.assert_called_once_with(f"{message}: {exception}", severity="error")

    def test_notify_warning(self):
        """Test warning notification."""
        message = "Warning message"
        self.command.notify_warning(message)

        self.app.notify.assert_called_once_with(message, severity="warning")


if __name__ == "__main__":
    unittest.main()
