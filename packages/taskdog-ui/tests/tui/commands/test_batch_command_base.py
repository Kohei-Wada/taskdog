"""Tests for BatchCommandBase."""

from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.batch_command_base import BatchCommandBase
from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)


def _make_bulk_output(
    task_ids: list[int],
    *,
    failures: dict[int, str] | None = None,
) -> BulkOperationOutput:
    """Helper to create BulkOperationOutput for tests."""
    failures = failures or {}
    results = []
    for tid in task_ids:
        if tid in failures:
            results.append(
                BulkTaskResultOutput(
                    task_id=tid, success=False, task=None, error=failures[tid]
                )
            )
        else:
            results.append(
                BulkTaskResultOutput(task_id=tid, success=True, task=None, error=None)
            )
    return BulkOperationOutput(results=results)


class ConcreteBatchCommand(BatchCommandBase):
    """Concrete implementation without confirmation for testing."""

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Execute bulk operation."""
        return _make_bulk_output(task_ids)


class ConcreteBatchCommandWithConfirmation(BatchCommandBase):
    """Concrete implementation with confirmation for testing."""

    def execute_bulk(self, task_ids: list[int]) -> BulkOperationOutput:
        """Execute bulk operation."""
        return _make_bulk_output(task_ids)

    def get_confirmation_config(self) -> tuple[str, str, str]:
        """Return confirmation config."""
        return (
            "Confirm Action",
            "Process this task?",
            "Process {count} tasks?",
        )


class TestBatchCommandBaseNoConfirmation:
    """Test cases for BatchCommandBase without confirmation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommand(self.mock_app, self.mock_context)

    def test_execute_warns_when_no_tasks_selected(self) -> None:
        """Test warning when no tasks are selected."""
        self.command.get_selected_task_ids = MagicMock(return_value=[])
        self.command.notify_warning = MagicMock()

        self.command.execute()

        self.command.notify_warning.assert_called_once()
        assert (
            "no tasks selected" in self.command.notify_warning.call_args[0][0].lower()
        )

    def test_execute_processes_single_task(self) -> None:
        """Test processing a single task."""
        self.command.get_selected_task_ids = MagicMock(return_value=[42])
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([42]))
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.execute_bulk.assert_called_once_with([42])
        self.command.clear_task_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()

    def test_execute_processes_multiple_tasks(self) -> None:
        """Test processing multiple tasks."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([1, 2, 3]))
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.execute_bulk.assert_called_once_with([1, 2, 3])

    def test_execute_handles_task_error(self) -> None:
        """Test error handling for failed task."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1], failures={1: "Task failed"})
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.notify_error.assert_called_once()
        self.command.clear_task_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()


class TestBatchCommandBaseProcessTasks:
    """Test cases for _process_tasks method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommand(self.mock_app, self.mock_context)

    def test_returns_correct_success_count(self) -> None:
        """Test that success count is correct."""
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([1, 2, 3]))

        success, failure = self.command._process_tasks([1, 2, 3])

        assert success == 3
        assert failure == 0

    def test_returns_correct_failure_count(self) -> None:
        """Test that failure count is correct."""
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1, 2], failures={1: "Error", 2: "Error"})
        )
        self.command.notify_error = MagicMock()

        success, failure = self.command._process_tasks([1, 2])

        assert success == 0
        assert failure == 2

    def test_returns_mixed_counts(self) -> None:
        """Test mixed success and failure counts."""
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1, 2, 3], failures={2: "Error"})
        )
        self.command.notify_error = MagicMock()

        success, failure = self.command._process_tasks([1, 2, 3])

        assert success == 2
        assert failure == 1


class TestBatchCommandBaseShowSummary:
    """Test cases for _show_summary method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommand(self.mock_app, self.mock_context)
        self.command.notify_warning = MagicMock()

    def test_no_summary_for_all_success(self) -> None:
        """Test no summary shown when all tasks succeed."""
        self.command._show_summary(success_count=3, failure_count=0)

        self.command.notify_warning.assert_not_called()

    def test_no_summary_for_single_task_failure(self) -> None:
        """Test no summary for single task failure (error already shown per-task)."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1], failures={1: "Task failed"})
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.notify_warning.assert_not_called()

    def test_shows_warning_for_partial_failure(self) -> None:
        """Test warning shown for partial failures."""
        self.command._show_summary(success_count=2, failure_count=1)

        self.command.notify_warning.assert_called_once()
        msg = self.command.notify_warning.call_args[0][0]
        assert "2 succeeded" in msg
        assert "1 failed" in msg


class TestBatchCommandBaseWithConfirmation:
    """Test cases for BatchCommandBase with confirmation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommandWithConfirmation(
            self.mock_app, self.mock_context
        )

    def test_execute_shows_confirmation_dialog(self) -> None:
        """Test that confirmation dialog is shown."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2])

        self.command.execute()

        self.mock_app.push_screen.assert_called_once()
        call_args = self.mock_app.push_screen.call_args
        dialog = call_args[0][0]
        assert dialog.title_text == "Confirm Action"

    def test_single_task_confirmation_message(self) -> None:
        """Test single task message is used for one task."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])

        self.command.execute()

        dialog = self.mock_app.push_screen.call_args[0][0]
        assert dialog.message_text == "Process this task?"

    def test_multiple_tasks_confirmation_message(self) -> None:
        """Test template is formatted for multiple tasks."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3, 4, 5])

        self.command.execute()

        dialog = self.mock_app.push_screen.call_args[0][0]
        assert dialog.message_text == "Process 5 tasks?"

    def test_does_nothing_when_cancelled(self) -> None:
        """Test that nothing happens when user cancels."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(False)

        self.command.execute_bulk.assert_not_called()

    def test_does_nothing_when_result_is_none(self) -> None:
        """Test that nothing happens when result is None."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(None)

        self.command.execute_bulk.assert_not_called()

    def test_executes_action_when_confirmed(self) -> None:
        """Test that action is executed when confirmed."""
        self.command.get_selected_task_ids = MagicMock(return_value=[42])
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([42]))
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.execute_bulk.assert_called_once_with([42])

    def test_executes_action_for_multiple_tasks(self) -> None:
        """Test that action is executed for all tasks."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([1, 2, 3]))
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.execute_bulk.assert_called_once_with([1, 2, 3])

    def test_clears_selection_after_execution(self) -> None:
        """Test that selection is cleared after execution."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([1]))
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.clear_task_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()

    def test_handles_task_not_found_error(self) -> None:
        """Test error handling for task not found in bulk result."""
        self.command.get_selected_task_ids = MagicMock(return_value=[999])
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([999], failures={999: "Task not found: 999"})
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_error.assert_called_once()

    def test_handles_task_validation_error(self) -> None:
        """Test error handling for validation error in bulk result."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1], failures={1: "Invalid operation"})
        )
        self.command.notify_error = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_error.assert_called_once()

    def test_handles_generic_exception(self) -> None:
        """Test error handling for generic error in bulk result."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1], failures={1: "Generic error"})
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
        self.command.execute_bulk = MagicMock(
            return_value=_make_bulk_output([1, 2, 3], failures={2: "Error"})
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
        self.command.execute_bulk = MagicMock(return_value=_make_bulk_output([1, 2]))
        self.command.notify_warning = MagicMock()
        self.command.clear_task_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback_wrapper = self.mock_app.push_screen.call_args[0][1]
        callback_wrapper(True)

        self.command.notify_warning.assert_not_called()


class TestBatchCommandBaseConfirmationConfig:
    """Test cases for confirmation config edge cases."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommandWithConfirmation(
            self.mock_app, self.mock_context
        )

    def test_raises_value_error_for_invalid_placeholder(self) -> None:
        """Test ValueError is raised for template with wrong placeholder."""
        self.command.get_confirmation_config = MagicMock(
            return_value=(
                "Title",
                "Single msg",
                "Process {num} tasks?",  # Wrong placeholder
            )
        )
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])

        with pytest.raises(ValueError) as exc_info:
            self.command.execute()

        assert "count" in str(exc_info.value).lower()
