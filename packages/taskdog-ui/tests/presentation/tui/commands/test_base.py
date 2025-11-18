"""Tests for TUICommandBase."""

import unittest
from unittest.mock import MagicMock

from taskdog.tui.commands.base import TUICommandBase
from taskdog_core.application.dto.get_task_by_id_output import TaskByIdOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class ConcreteCommand(TUICommandBase):
    """Concrete command for testing."""

    def execute(self) -> None:
        """Dummy execute implementation."""
        pass


class ConcreteCommandWithImpl(TUICommandBase):
    """Concrete command that uses execute_impl pattern."""

    def __init__(self, app, context, should_raise=False):
        """Initialize with optional error behavior."""
        super().__init__(app, context)
        self.should_raise = should_raise
        self.executed = False

    def execute_impl(self) -> None:
        """Implementation that can optionally raise an error."""
        self.executed = True
        if self.should_raise:
            raise ValueError("Test error from execute_impl")


class TestTUICommandBase(unittest.TestCase):
    """Test cases for TUICommandBase."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = MagicMock()
        self.app.main_screen = MagicMock()
        self.context = MagicMock()
        self.command = ConcreteCommand(self.app, self.context)

    def test_initialization(self):
        """Test command initialization."""
        self.assertEqual(self.command.app, self.app)
        self.assertEqual(self.command.context, self.context)

    def test_get_selected_task_success(self):
        """Test getting selected task successfully."""
        task = Task(id=1, name="Test Task", priority=5, status=TaskStatus.PENDING)
        # Create TaskDetailDto from task
        task_dto = TaskDetailDto(
            id=task.id,
            name=task.name,
            priority=task.priority,
            status=task.status,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            estimated_duration=None,
            daily_allocations={},
            is_fixed=False,
            depends_on=[],
            actual_daily_hours={},
            tags=[],
            is_archived=False,
            created_at=task.created_at,
            updated_at=task.updated_at,
            actual_duration_hours=None,
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=False,
        )
        # Mock get_selected_task_id to return the task ID
        self.app.main_screen.task_table.get_selected_task_id.return_value = 1
        # Mock API client to return the TaskByIdOutput
        self.context.api_client.get_task_by_id.return_value = TaskByIdOutput(
            task=task_dto
        )

        result = self.command.get_selected_task()

        self.assertEqual(result, task_dto)
        self.context.api_client.get_task_by_id.assert_called_once_with(1)

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

        self.app.notify.assert_called_once_with(
            f"{message}: {exception}", severity="error"
        )

    def test_notify_warning(self):
        """Test warning notification."""
        message = "Warning message"
        self.command.notify_warning(message)

        self.app.notify.assert_called_once_with(message, severity="warning")

    def test_execute_impl_success(self):
        """Test execute() with execute_impl() that succeeds."""
        command = ConcreteCommandWithImpl(self.app, self.context, should_raise=False)
        command.execute()

        # Verify execute_impl was called
        self.assertTrue(command.executed)
        # Verify no error notification
        self.app.notify.assert_not_called()

    def test_execute_impl_with_error_handling(self):
        """Test execute() with execute_impl() that raises an error."""
        command = ConcreteCommandWithImpl(self.app, self.context, should_raise=True)
        command.execute()

        # Verify execute_impl was called
        self.assertTrue(command.executed)
        # Verify error notification was shown
        self.app.notify.assert_called_once()
        call_args = self.app.notify.call_args
        self.assertIn("Error", call_args[0][0])
        self.assertIn("Test error from execute_impl", call_args[0][0])
        self.assertEqual(call_args[1]["severity"], "error")

    def test_get_action_name_default(self):
        """Test get_action_name() derives from class name."""
        command = ConcreteCommandWithImpl(self.app, self.context)
        action_name = command.get_action_name()

        # "ConcreteCommandWithImpl" -> "concrete command with impl"
        self.assertIn("concrete", action_name)
        self.assertIn("command", action_name)

    def test_handle_error_wrapper_success(self):
        """Test handle_error() wrapper with successful callback."""
        called = []

        def callback(value):
            called.append(value)
            return value * 2

        wrapped = self.command.handle_error(callback)
        result = wrapped(5)

        self.assertEqual(result, 10)
        self.assertEqual(called, [5])
        # No error notification
        self.app.notify.assert_not_called()

    def test_handle_error_wrapper_with_exception(self):
        """Test handle_error() wrapper with callback that raises exception."""

        def callback(value):
            raise ValueError(f"Test error with {value}")

        wrapped = self.command.handle_error(callback)
        result = wrapped(5)

        # Should return None on error
        self.assertIsNone(result)
        # Should show error notification
        self.app.notify.assert_called_once()
        call_args = self.app.notify.call_args
        self.assertIn("Error", call_args[0][0])
        self.assertIn("Test error with 5", call_args[0][0])
        self.assertEqual(call_args[1]["severity"], "error")

    def test_manage_dependencies_add_only(self):
        """Test manage_dependencies() with only adding dependencies."""
        # Mock successful API calls
        self.context.api_client.add_dependency.return_value = None

        failures = self.command.manage_dependencies(task_id=1, add_deps=[2, 3, 4])

        # Verify no failures
        self.assertEqual(failures, [])
        # Verify add_dependency called for each dep
        self.assertEqual(self.context.api_client.add_dependency.call_count, 3)
        self.context.api_client.add_dependency.assert_any_call(1, 2)
        self.context.api_client.add_dependency.assert_any_call(1, 3)
        self.context.api_client.add_dependency.assert_any_call(1, 4)

    def test_manage_dependencies_remove_only(self):
        """Test manage_dependencies() with only removing dependencies."""
        # Mock successful API calls
        self.context.api_client.remove_dependency.return_value = None

        failures = self.command.manage_dependencies(task_id=1, remove_deps=[2, 3])

        # Verify no failures
        self.assertEqual(failures, [])
        # Verify remove_dependency called for each dep
        self.assertEqual(self.context.api_client.remove_dependency.call_count, 2)
        self.context.api_client.remove_dependency.assert_any_call(1, 2)
        self.context.api_client.remove_dependency.assert_any_call(1, 3)

    def test_manage_dependencies_add_and_remove(self):
        """Test manage_dependencies() with both adding and removing."""
        # Mock successful API calls
        self.context.api_client.add_dependency.return_value = None
        self.context.api_client.remove_dependency.return_value = None

        failures = self.command.manage_dependencies(
            task_id=1, add_deps=[4, 5], remove_deps=[2, 3]
        )

        # Verify no failures
        self.assertEqual(failures, [])
        # Verify remove operations happen first
        self.assertEqual(self.context.api_client.remove_dependency.call_count, 2)
        self.context.api_client.remove_dependency.assert_any_call(1, 2)
        self.context.api_client.remove_dependency.assert_any_call(1, 3)
        # Then add operations
        self.assertEqual(self.context.api_client.add_dependency.call_count, 2)
        self.context.api_client.add_dependency.assert_any_call(1, 4)
        self.context.api_client.add_dependency.assert_any_call(1, 5)

    def test_manage_dependencies_with_failures(self):
        """Test manage_dependencies() with some operations failing."""

        # Mock add_dependency to fail for dep 3
        def add_side_effect(task_id, dep_id):
            if dep_id == 3:
                raise TaskValidationError("Circular dependency detected")
            return None

        # Mock remove_dependency to fail for dep 2
        def remove_side_effect(task_id, dep_id):
            if dep_id == 2:
                raise TaskValidationError("Dependency not found")
            return None

        self.context.api_client.add_dependency.side_effect = add_side_effect
        self.context.api_client.remove_dependency.side_effect = remove_side_effect

        failures = self.command.manage_dependencies(
            task_id=1, add_deps=[3, 4], remove_deps=[2, 5]
        )

        # Verify we got 2 failure messages
        self.assertEqual(len(failures), 2)
        self.assertIn("Remove 2: Dependency not found", failures)
        self.assertIn("Add 3: Circular dependency detected", failures)

    def test_manage_dependencies_no_operations(self):
        """Test manage_dependencies() with no operations."""
        failures = self.command.manage_dependencies(task_id=1)

        # Verify no failures and no API calls
        self.assertEqual(failures, [])
        self.context.api_client.add_dependency.assert_not_called()
        self.context.api_client.remove_dependency.assert_not_called()


if __name__ == "__main__":
    unittest.main()
