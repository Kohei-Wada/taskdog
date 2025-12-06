"""Tests for BatchStatusChangeCommandBase."""

from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.batch_status_change_base import BatchStatusChangeCommandBase
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


def create_mock_output(task_id: int = 1, name: str = "Task") -> MagicMock:
    """Create a mock TaskOperationOutput."""
    mock = MagicMock(spec=TaskOperationOutput)
    mock.id = task_id
    mock.name = name
    return mock


class ConcreteBatchCommand(BatchStatusChangeCommandBase):
    """Concrete implementation for testing."""

    def execute_single_task(self, task_id: int) -> TaskOperationOutput:
        """Execute on single task."""
        mock = MagicMock(spec=TaskOperationOutput)
        mock.id = task_id
        mock.name = f"Task {task_id}"
        return mock

    def get_success_message(self, task_name: str, task_id: int) -> str:
        """Get success message."""
        return f"Completed: {task_name} (ID: {task_id})"


class TestBatchStatusChangeCommandBase:
    """Test cases for BatchStatusChangeCommandBase."""

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
        self.command.execute_single_task = MagicMock(
            return_value=create_mock_output(task_id=42, name="Task 42")
        )
        self.command.clear_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.execute_single_task.assert_called_once_with(42)
        self.command.clear_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()

    def test_execute_processes_multiple_tasks(self) -> None:
        """Test processing multiple tasks."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1, 2, 3])
        self.command.execute_single_task = MagicMock(
            side_effect=[
                create_mock_output(task_id=1, name="Task 1"),
                create_mock_output(task_id=2, name="Task 2"),
                create_mock_output(task_id=3, name="Task 3"),
            ]
        )
        self.command.clear_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        assert self.command.execute_single_task.call_count == 3

    def test_execute_handles_task_error(self) -> None:
        """Test error handling for failed task."""
        self.command.get_selected_task_ids = MagicMock(return_value=[1])
        self.command.execute_single_task = MagicMock(
            side_effect=Exception("Task failed")
        )
        self.command.notify_error = MagicMock()
        self.command.clear_selection = MagicMock()
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        self.command.notify_error.assert_called_once()
        # Should still clear selection and reload
        self.command.clear_selection.assert_called_once()
        self.command.reload_tasks.assert_called_once()


class TestBatchStatusChangeCommandProcessTasks:
    """Test cases for _process_tasks method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommand(self.mock_app, self.mock_context)

    def test_returns_correct_success_count(self) -> None:
        """Test that success count is correct."""
        self.command.execute_single_task = MagicMock(
            return_value=create_mock_output(task_id=1, name="Task")
        )

        success, failure = self.command._process_tasks([1, 2, 3])

        assert success == 3
        assert failure == 0

    def test_returns_correct_failure_count(self) -> None:
        """Test that failure count is correct."""
        self.command.execute_single_task = MagicMock(side_effect=Exception("Error"))
        self.command.notify_error = MagicMock()

        success, failure = self.command._process_tasks([1, 2])

        assert success == 0
        assert failure == 2

    def test_returns_mixed_counts(self) -> None:
        """Test mixed success and failure counts."""
        self.command.execute_single_task = MagicMock(
            side_effect=[
                create_mock_output(task_id=1, name="Task 1"),
                Exception("Error"),
                create_mock_output(task_id=3, name="Task 3"),
            ]
        )
        self.command.notify_error = MagicMock()

        success, failure = self.command._process_tasks([1, 2, 3])

        assert success == 2
        assert failure == 1


class TestBatchStatusChangeCommandShowSummary:
    """Test cases for _show_summary method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ConcreteBatchCommand(self.mock_app, self.mock_context)
        self.command.notify_warning = MagicMock()

    def test_no_summary_for_single_task_success(self) -> None:
        """Test no summary shown for single task success."""
        self.command._show_summary([1], success_count=1, failure_count=0)

        self.command.notify_warning.assert_not_called()

    def test_no_summary_for_single_task_failure(self) -> None:
        """Test no summary shown for single task failure."""
        self.command._show_summary([1], success_count=0, failure_count=1)

        self.command.notify_warning.assert_not_called()

    def test_no_summary_for_all_success(self) -> None:
        """Test no summary shown when all tasks succeed."""
        self.command._show_summary([1, 2, 3], success_count=3, failure_count=0)

        self.command.notify_warning.assert_not_called()

    def test_shows_warning_for_partial_failure(self) -> None:
        """Test warning shown for partial failures."""
        self.command._show_summary([1, 2, 3], success_count=2, failure_count=1)

        self.command.notify_warning.assert_called_once()
        msg = self.command.notify_warning.call_args[0][0]
        assert "2 succeeded" in msg
        assert "1 failed" in msg
