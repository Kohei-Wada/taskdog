"""Tests for BatchCommandExecutor."""

import unittest
from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.batch_executor import BatchCommandExecutor


class TestBatchCommandExecutor(unittest.TestCase):
    """Test cases for BatchCommandExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        # Create console with StringIO buffer to capture output
        # Disable color/markup to make testing easier
        self.output = StringIO()
        self.console = Console(
            file=self.output, force_terminal=False, width=80, legacy_windows=False
        )
        self.executor = BatchCommandExecutor(self.console)

    def test_execute_batch_single_task_success(self):
        """Test batch execution with single task succeeds."""
        process_func = MagicMock(return_value="result")
        success_callback = MagicMock()

        success_count, error_count, results = self.executor.execute_batch(
            task_ids=(1,),
            process_func=process_func,
            operation_name="testing",
            success_callback=success_callback,
        )

        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 0)
        self.assertEqual(results, ["result"])
        process_func.assert_called_once_with(1)
        success_callback.assert_called_once_with("result")

    def test_execute_batch_multiple_tasks_success(self):
        """Test batch execution with multiple tasks succeeds."""
        process_func = MagicMock(side_effect=["result1", "result2", "result3"])
        success_callback = MagicMock()

        success_count, error_count, results = self.executor.execute_batch(
            task_ids=(1, 2, 3),
            process_func=process_func,
            operation_name="testing",
            success_callback=success_callback,
        )

        self.assertEqual(success_count, 3)
        self.assertEqual(error_count, 0)
        self.assertEqual(results, ["result1", "result2", "result3"])
        self.assertEqual(process_func.call_count, 3)
        self.assertEqual(success_callback.call_count, 3)

        # Verify summary is shown for multiple tasks
        output = self.output.getvalue()
        self.assertIn("Successfully", output)
        self.assertIn("3 task(s)", output)

    def test_execute_batch_task_not_found_error(self):
        """Test batch execution handles TaskNotFoundException."""

        def process_with_error(task_id):
            if task_id == 2:
                raise TaskNotFoundException(task_id=2)
            return f"result{task_id}"

        process_func = MagicMock(side_effect=process_with_error)

        success_count, error_count, results = self.executor.execute_batch(
            task_ids=(1, 2, 3),
            process_func=process_func,
            operation_name="testing",
            show_summary=False,  # Disable summary to simplify output check
        )

        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 1)
        self.assertEqual(len(results), 2)

        # Verify error message is shown
        output = self.output.getvalue()
        self.assertIn("Task 2 not found", output)

    def test_execute_batch_custom_error_handler(self):
        """Test batch execution uses custom error handlers."""

        class CustomError(Exception):
            pass

        def process_with_custom_error(task_id):
            if task_id == 2:
                raise CustomError("Custom error")
            return f"result{task_id}"

        process_func = MagicMock(side_effect=process_with_custom_error)
        custom_handler = MagicMock()

        success_count, error_count, _results = self.executor.execute_batch(
            task_ids=(1, 2, 3),
            process_func=process_func,
            operation_name="testing",
            error_handlers={CustomError: custom_handler},
            show_summary=False,
        )

        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 1)
        custom_handler.assert_called_once()

    def test_execute_batch_default_error_handler(self):
        """Test batch execution uses default error handler for unhandled exceptions."""

        def process_with_error(task_id):
            if task_id == 2:
                raise ValueError("Some error")
            return f"result{task_id}"

        process_func = MagicMock(side_effect=process_with_error)

        success_count, error_count, _results = self.executor.execute_batch(
            task_ids=(1, 2, 3),
            process_func=process_func,
            operation_name="testing",
            show_summary=False,
        )

        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 1)

        # Verify default error message is shown
        output = self.output.getvalue()
        self.assertIn("Error testing", output)
        self.assertIn("Some error", output)

    def test_execute_batch_no_summary_for_single_task(self):
        """Test no summary shown for single task."""
        process_func = MagicMock(return_value="result")

        self.executor.execute_batch(
            task_ids=(1,),
            process_func=process_func,
            operation_name="testing",
        )

        output = self.output.getvalue()
        # Summary should not contain "Successfully X task(s)" pattern
        self.assertNotIn("task(s)", output)

    def test_execute_batch_summary_disabled(self):
        """Test summary can be disabled with show_summary=False."""
        process_func = MagicMock(side_effect=["result1", "result2"])

        self.executor.execute_batch(
            task_ids=(1, 2),
            process_func=process_func,
            operation_name="testing",
            show_summary=False,
        )

        output = self.output.getvalue()
        # No summary should be shown
        self.assertNotIn("Successfully", output)

    def test_execute_batch_summary_with_errors(self):
        """Test summary shows mixed results correctly."""

        def process_with_error(task_id):
            if task_id in [2, 4]:
                raise ValueError("Error")
            return f"result{task_id}"

        process_func = MagicMock(side_effect=process_with_error)

        success_count, error_count, _ = self.executor.execute_batch(
            task_ids=(1, 2, 3, 4),
            process_func=process_func,
            operation_name="testing",
        )

        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 2)

        output = self.output.getvalue()
        self.assertIn("2 task(s)", output)
        self.assertIn("2 error(s)", output)

    def test_execute_batch_summary_all_errors(self):
        """Test summary when all tasks fail."""

        def process_with_error(task_id):
            raise ValueError("Error")

        process_func = MagicMock(side_effect=process_with_error)

        success_count, error_count, _ = self.executor.execute_batch(
            task_ids=(1, 2, 3),
            process_func=process_func,
            operation_name="testing",
        )

        self.assertEqual(success_count, 0)
        self.assertEqual(error_count, 3)

        output = self.output.getvalue()
        self.assertIn("Failed to testing 3 task(s)", output)

    def test_execute_batch_success_callback_receives_result(self):
        """Test success callback receives correct result."""
        results_received = []

        def success_callback(result):
            results_received.append(result)

        process_func = MagicMock(side_effect=["result1", "result2"])

        self.executor.execute_batch(
            task_ids=(1, 2),
            process_func=process_func,
            operation_name="testing",
            success_callback=success_callback,
        )

        self.assertEqual(results_received, ["result1", "result2"])


if __name__ == "__main__":
    unittest.main()
