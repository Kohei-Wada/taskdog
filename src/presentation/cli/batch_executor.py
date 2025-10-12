"""Batch command executor for consistent batch processing across commands."""

from collections.abc import Callable
from typing import Any

from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_error, print_task_not_found_error


class BatchCommandExecutor:
    """Handles batch execution of commands with consistent error handling and reporting.

    Provides a unified pattern for processing multiple task IDs with:
    - Automatic error handling per task
    - Progress tracking (success/error counts)
    - Spacing between tasks when processing multiple IDs
    - Summary reporting
    - Customizable success/error callbacks
    """

    def __init__(self, console):
        """Initialize batch executor.

        Args:
            console: Rich Console instance for output
        """
        self.console = console

    def execute_batch(
        self,
        task_ids: tuple[int, ...],
        process_func: Callable[[int], Any],
        operation_name: str,
        success_callback: Callable[[Any], None] | None = None,
        error_handlers: dict[type[Exception], Callable[[Exception], None]] | None = None,
        show_summary: bool = True,
    ) -> tuple[int, int, list[Any]]:
        """Execute operation on multiple task IDs with consistent error handling.

        Args:
            task_ids: Tuple of task IDs to process
            process_func: Function to call for each task ID (receives task_id, returns result)
            operation_name: Name of operation for error messages (e.g., "starting task")
            success_callback: Optional callback for successful operations (receives result)
            error_handlers: Optional dict mapping exception types to handler functions
            show_summary: Whether to show summary after batch operation (default: True)

        Returns:
            Tuple of (success_count, error_count, results_list)

        Example:
            >>> executor = BatchCommandExecutor(console)
            >>> def process(task_id):
            ...     return use_case.execute(Input(task_id=task_id))
            >>> def on_success(task):
            ...     console.print(f"Task {task.id} completed!")
            >>> success, errors, results = executor.execute_batch(
            ...     task_ids=(1, 2, 3),
            ...     process_func=process,
            ...     operation_name="processing task",
            ...     success_callback=on_success
            ... )
        """
        success_count = 0
        error_count = 0
        results = []

        for task_id in task_ids:
            try:
                result = process_func(task_id)
                results.append(result)
                success_count += 1

                # Call success callback if provided
                if success_callback:
                    success_callback(result)

                # Add spacing between tasks if processing multiple
                if len(task_ids) > 1:
                    self.console.print()

            except TaskNotFoundException as e:
                print_task_not_found_error(self.console, e.task_id)
                error_count += 1
                if len(task_ids) > 1:
                    self.console.print()

            except Exception as e:
                # Check for custom error handlers
                handled = False
                if error_handlers:
                    for exc_type, handler in error_handlers.items():
                        if isinstance(e, exc_type):
                            handler(e)
                            handled = True
                            break

                # Use default error handling if no custom handler matched
                if not handled:
                    print_error(self.console, operation_name, e)

                error_count += 1
                if len(task_ids) > 1:
                    self.console.print()

        # Show summary if multiple tasks were processed
        if show_summary and len(task_ids) > 1:
            self._print_summary(success_count, error_count, operation_name)

        return success_count, error_count, results

    def _print_summary(self, success_count: int, error_count: int, operation_name: str) -> None:
        """Print summary of batch operation results.

        Args:
            success_count: Number of successful operations
            error_count: Number of failed operations
            operation_name: Name of the operation for the summary message
        """
        # Convert operation_name to past tense for summary
        # Simple heuristic: most operation names end with "ing"
        # e.g., "starting task" -> "started", "removing task" -> "removed"
        if operation_name.endswith("ing task"):
            past_tense = operation_name.replace("ing task", "ed")
        elif operation_name.endswith("ing"):
            past_tense = operation_name[:-3] + "ed"
        else:
            past_tense = operation_name

        if success_count > 0 and error_count == 0:
            self.console.print(
                f"[green]✓[/green] Successfully {past_tense} {success_count} task(s)"
            )
        elif success_count > 0 and error_count > 0:
            self.console.print(
                f"[yellow]⚠[/yellow] {past_tense.capitalize()} {success_count} task(s), {error_count} error(s)"
            )
        elif error_count > 0:
            self.console.print(f"[red]✗[/red] Failed to {operation_name} {error_count} task(s)")
