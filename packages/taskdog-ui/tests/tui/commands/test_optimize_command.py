"""Tests for OptimizeCommand."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.optimize_command import OptimizeCommand
from taskdog_core.application.dto.optimization_output import (
    OptimizationOutput,
    SchedulingFailure,
)
from taskdog_core.application.dto.optimization_summary import OptimizationSummary
from taskdog_core.application.dto.task_dto import TaskSummaryDto


def create_mock_task_summary(task_id: int = 1, name: str = "Task") -> TaskSummaryDto:
    """Create a mock TaskSummaryDto."""
    return TaskSummaryDto(id=task_id, name=name)


def create_mock_scheduling_failure(
    task_id: int = 1, name: str = "Task", reason: str = "No available slots"
) -> SchedulingFailure:
    """Create a mock SchedulingFailure."""
    task = create_mock_task_summary(task_id, name)
    return SchedulingFailure(task=task, reason=reason)


def create_mock_optimization_output(
    successful_count: int = 0,
    failed_tasks: list[SchedulingFailure] | None = None,
) -> OptimizationOutput:
    """Create a mock OptimizationOutput."""
    successful_tasks = [
        create_mock_task_summary(i, f"Success Task {i}")
        for i in range(1, successful_count + 1)
    ]
    summary = MagicMock(spec=OptimizationSummary)
    return OptimizationOutput(
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks or [],
        daily_allocations={date(2025, 1, 6): 4.0},
        summary=summary,
        task_states_before={},
    )


class TestOptimizeCommandInit:
    """Test cases for OptimizeCommand initialization."""

    def test_inherits_from_base(self) -> None:
        """Test that OptimizeCommand inherits from TUICommandBase."""
        mock_app = MagicMock()
        mock_context = MagicMock()

        command = OptimizeCommand(mock_app, mock_context)

        assert command.app is mock_app
        assert command.context is mock_context


class TestOptimizeCommandFormatFailedTasksMessage:
    """Test cases for _format_failed_tasks_message method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = OptimizeCommand(self.mock_app, self.mock_context)

    def test_shows_details_for_few_failures(self) -> None:
        """Test detailed message when failures <= threshold (5)."""
        failures = [
            create_mock_scheduling_failure(1, "Task A", "Deadline too early"),
            create_mock_scheduling_failure(2, "Task B", "No slots available"),
        ]
        result = create_mock_optimization_output(failed_tasks=failures)

        message = self.command._format_failed_tasks_message(result)

        assert "2 task(s) failed:" in message
        assert "#1 Task A: Deadline too early" in message
        assert "#2 Task B: No slots available" in message

    def test_shows_details_at_threshold(self) -> None:
        """Test detailed message when failures == threshold (5)."""
        failures = [
            create_mock_scheduling_failure(i, f"Task {i}", f"Reason {i}")
            for i in range(1, 6)
        ]
        result = create_mock_optimization_output(failed_tasks=failures)

        message = self.command._format_failed_tasks_message(result)

        assert "5 task(s) failed:" in message
        for i in range(1, 6):
            assert f"#${i} Task {i}" in message or f"Task {i}" in message

    def test_shows_summary_above_threshold(self) -> None:
        """Test summary message when failures > threshold (5)."""
        failures = [
            create_mock_scheduling_failure(i, f"Task {i}", f"Reason {i}")
            for i in range(1, 8)
        ]
        result = create_mock_optimization_output(failed_tasks=failures)

        message = self.command._format_failed_tasks_message(result)

        assert "7 tasks failed to schedule" in message
        assert "Check gantt chart for details" in message
        # Should NOT include detailed task list
        assert "Task 1:" not in message

    def test_includes_prefix_in_message(self) -> None:
        """Test that prefix is included in message."""
        failures = [create_mock_scheduling_failure(1, "Task", "Reason")]
        result = create_mock_optimization_output(failed_tasks=failures)

        message = self.command._format_failed_tasks_message(
            result, prefix="Partially done. "
        )

        assert message.startswith("Partially done. ")

    def test_empty_failures_returns_zero_count(self) -> None:
        """Test message with empty failures list."""
        result = create_mock_optimization_output(failed_tasks=[])

        message = self.command._format_failed_tasks_message(result)

        assert "0 task(s) failed:" in message


class TestOptimizeCommandExecute:
    """Test cases for execute method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = OptimizeCommand(self.mock_app, self.mock_context)

    def test_pushes_algorithm_selection_dialog(self) -> None:
        """Test that execute pushes the algorithm selection dialog."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = [
            ("greedy", "Greedy", "Simple greedy algorithm")
        ]

        self.command.execute()

        self.mock_app.push_screen.assert_called_once()
        call_args = self.mock_app.push_screen.call_args
        from taskdog.tui.dialogs.algorithm_selection_dialog import (
            AlgorithmSelectionDialog,
        )

        assert isinstance(call_args[0][0], AlgorithmSelectionDialog)

    def test_does_nothing_when_cancelled(self) -> None:
        """Test that nothing happens when user cancels dialog."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []

        self.command.execute()

        # Get the callback passed to push_screen
        callback = self.mock_app.push_screen.call_args[0][1]
        # Simulate cancellation
        callback(None)

        self.mock_context.api_client.optimize_schedule.assert_not_called()

    def test_calls_optimize_schedule_with_settings(self) -> None:
        """Test that optimize_schedule is called with correct settings."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        result = create_mock_optimization_output(successful_count=3)
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        start_date = datetime(2025, 1, 6)
        callback(("balanced", 6.0, start_date, True))

        self.mock_context.api_client.optimize_schedule.assert_called_once_with(
            algorithm="balanced",
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=True,
        )

    def test_reloads_tasks_after_optimization(self) -> None:
        """Test that tasks are reloaded after optimization."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        result = create_mock_optimization_output(successful_count=1)
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        callback(("greedy", None, datetime.now(), False))

        self.command.reload_tasks.assert_called_once()

    def test_warns_when_all_failed(self) -> None:
        """Test warning message when all tasks fail."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        failures = [create_mock_scheduling_failure(1, "Task", "No slots")]
        result = create_mock_optimization_output(failed_tasks=failures)
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()
        self.command.notify_warning = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        callback(("greedy", 8.0, datetime.now(), False))

        self.command.notify_warning.assert_called_once()
        message = self.command.notify_warning.call_args[0][0]
        assert "No tasks were optimized" in message

    def test_warns_on_partial_failure(self) -> None:
        """Test warning message when some tasks fail."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        failures = [create_mock_scheduling_failure(10, "Failed Task", "No slots")]
        result = create_mock_optimization_output(
            successful_count=2, failed_tasks=failures
        )
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()
        self.command.notify_warning = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        callback(("balanced", 8.0, datetime.now(), True))

        self.command.notify_warning.assert_called_once()
        message = self.command.notify_warning.call_args[0][0]
        assert "Partially optimized" in message
        assert "2 succeeded" in message

    def test_warns_when_no_tasks_optimized_empty_result(self) -> None:
        """Test warning when result has no successful tasks and no failures."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        result = create_mock_optimization_output(successful_count=0, failed_tasks=[])
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()
        self.command.notify_warning = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        callback(("greedy", None, datetime.now(), False))

        self.command.notify_warning.assert_called_once()
        message = self.command.notify_warning.call_args[0][0]
        assert "No tasks were optimized" in message
        assert "Check task requirements" in message

    def test_no_notification_on_full_success(self) -> None:
        """Test that no warning notification is shown on full success."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        result = create_mock_optimization_output(successful_count=5, failed_tasks=[])
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()
        self.command.notify_warning = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        callback(("greedy", 8.0, datetime.now(), False))

        self.command.notify_warning.assert_not_called()

    def test_passes_none_max_hours_to_api(self) -> None:
        """Test that None max_hours is passed correctly to API."""
        self.mock_context.api_client.get_algorithm_metadata.return_value = []
        result = create_mock_optimization_output(successful_count=1)
        self.mock_context.api_client.optimize_schedule.return_value = result
        self.command.reload_tasks = MagicMock()

        self.command.execute()

        callback = self.mock_app.push_screen.call_args[0][1]
        start_date = datetime(2025, 1, 6)
        callback(("greedy", None, start_date, False))  # max_hours is None

        call_kwargs = self.mock_context.api_client.optimize_schedule.call_args
        assert call_kwargs[1]["max_hours_per_day"] is None
