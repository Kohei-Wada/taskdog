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
        self.app.main_screen = MagicMock()
        self.context = MagicMock()
        self.task_service = MagicMock()
        self.command = ConcreteCommand(self.app, self.context, self.task_service)

    def test_initialization(self):
        """Test command initialization."""
        self.assertEqual(self.command.app, self.app)
        self.assertEqual(self.command.context, self.context)
        self.assertEqual(self.command.task_service, self.task_service)

    def test_get_selected_task_success(self):
        """Test getting selected task successfully."""
        expected_task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)
        # Mock get_selected_task_id to return the task ID
        self.app.main_screen.task_table.get_selected_task_id.return_value = 1
        # Mock repository to return the expected task
        self.context.repository.get_by_id.return_value = expected_task

        result = self.command.get_selected_task()

        self.assertEqual(result, expected_task)
        self.context.repository.get_by_id.assert_called_once_with(1)

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
        """Test reloading tasks posts TasksRefreshed event."""
        self.command.reload_tasks()

        # Verify that TasksRefreshed event was posted
        self.app.post_message.assert_called_once()
        posted_event = self.app.post_message.call_args[0][0]
        self.assertEqual(type(posted_event).__name__, "TasksRefreshed")

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
