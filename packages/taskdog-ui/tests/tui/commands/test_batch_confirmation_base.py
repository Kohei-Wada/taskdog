"""Tests for BatchConfirmationCommandBase."""

from unittest.mock import MagicMock, call

import pytest

from taskdog.tui.commands.batch_confirmation_base import BatchConfirmationCommandBase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class ConcreteBatchConfirmCommand(BatchConfirmationCommandBase):
    """Concrete implementation for testing."""

    def get_confirmation_title(self) -> str:
        """Return dialog title."""
        return "Confirm Action"

    def get_single_task_confirmation(self) -> str:
        """Return single task message."""
        return "Process this task?"

    def get_multiple_tasks_confirmation_template(self) -> str:
        """Return multi-task template."""
        return "Process {count} tasks?"

    def execute_confirmed_action(self, task_id: int) -> None:
        """Execute the action."""
        pass  # Will be mocked


class TestBatchConfirmationCommandBase:
    """Test cases for BatchConfirmationCommandBase."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchConfirmCommand(self.mock_app, self.mock_context)

    def test_execute_warns_when_no_tasks_selected(self) -> None:
        """Test warning when no tasks are selected."""
        self.command.get_selected_task_ids = MagicMock(return_value=[])
        self.command.notify_warning = MagicMock()

        self.command.execute()

        self.command.notify_warning.assert_called_once()
        assert (
            "no tasks selected" in self.command.notify_warning.call_args[0][0].lower()
        )

    def test_execute_shows_confirmation_dialog(self) -> None:
        """Test that confirmation dialog is shown."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2])

        self.command.execute()

        self.mock_app.push_screen.assert_called_once()
        call_args = self.mock_app.push_screen.call_args
        dialog = call_args[0][0]
        # ConfirmationDialog stores title in title_text attribute
        assert dialog.title_text == "Confirm Action"


class TestBatchConfirmationCommandGetConfirmationMessage:
    """Test cases for get_confirmation_message method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchConfirmCommand(self.mock_app, self.mock_context)

    def test_returns_single_task_message_for_count_1(self) -> None:
        """Test single task message is used for count=1."""
        result = self.command.get_confirmation_message(1)

        assert result == "Process this task?"

    def test_returns_formatted_template_for_multiple_tasks(self) -> None:
        """Test template is formatted for multiple tasks."""
        result = self.command.get_confirmation_message(5)

        assert result == "Process 5 tasks?"

    def test_raises_value_error_for_invalid_placeholder(self) -> None:
        """Test ValueError is raised for template with wrong placeholder."""
        # Override to return template with wrong placeholder
        self.command.get_multiple_tasks_confirmation_template = MagicMock(
            return_value="Process {num} tasks?"  # Using {num} instead of {count}
        )

        with pytest.raises(ValueError) as exc_info:
            self.command.get_confirmation_message(3)

        assert "count" in str(exc_info.value).lower()


class TestBatchConfirmationCommandConfirmationHandler:
    """Test cases for confirmation handler behavior."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchConfirmCommand(self.mock_app, self.mock_context)

    def test_does_nothing_when_cancelled(self) -> None:
        """Test that nothing happens when user cancels."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_confirmed_action = MagicMock()

        self.command.execute()

        # Get the callback and simulate cancel
        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(False)

        self.command.execute_confirmed_action.assert_not_called()

    def test_does_nothing_when_result_is_none(self) -> None:
        """Test that nothing happens when result is None."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_confirmed_action = MagicMock()

        self.command.execute()

        # Get the callback and simulate None result
        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(None)

        self.command.execute_confirmed_action.assert_not_called()

    def test_executes_action_when_confirmed(self) -> None:
        """Test that action is executed when confirmed."""
        self.command.get_selected_task_ids = MagicMock(return_value=[42])
        self.command.execute_confirmed_action = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        # Get the callback and simulate confirm
        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.execute_confirmed_action.assert_called_once_with(42)

    def test_executes_action_for_multiple_tasks(self) -> None:
        """Test that action is executed for all tasks."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])
        self.command.execute_confirmed_action = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        assert self.command.execute_confirmed_action.call_count == 3
        self.command.execute_confirmed_action.assert_has_calls(
            [call(1), call(2), call(3)]
        )

    def test_clears_selection_after_execution(self) -> None:
        """Test that selection is cleared after execution."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_confirmed_action = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.clear_task_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()

    def test_handles_task_not_found_error(self) -> None:
        """Test error handling for TaskNotFoundException."""
        self.command.get_selected_task_ids = MagicMock(return_value=[999])
        self.command.execute_confirmed_action = MagicMock(
            side_effect=TaskNotFoundException(999)
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_error.assert_called_once()

    def test_handles_task_validation_error(self) -> None:
        """Test error handling for TaskValidationError."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_confirmed_action = MagicMock(
            side_effect=TaskValidationError("Invalid operation")
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_error.assert_called_once()

    def test_handles_generic_exception(self) -> None:
        """Test error handling for generic exceptions."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_confirmed_action = MagicMock(
            side_effect=Exception("Generic error")
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_error.assert_called_once()

    def test_shows_warning_on_partial_failure(self) -> None:
        """Test warning is shown when some tasks fail."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])
        self.command.execute_confirmed_action = MagicMock(
            side_effect=[None, Exception("Error"), None]
        )
        self.command.notify_error = MagicMock()
        self.command.notify_warning = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_warning.assert_called_once()
        msg = self.command.notify_warning.call_args[0][0]
        assert "2 succeeded" in msg
        assert "1 failed" in msg

    def test_no_warning_when_all_succeed(self) -> None:
        """Test no warning when all tasks succeed."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2])
        self.command.execute_confirmed_action = MagicMock()
        self.command.notify_warning = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_warning.assert_not_called()
