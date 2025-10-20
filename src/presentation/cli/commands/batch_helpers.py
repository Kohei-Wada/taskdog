"""Helper functions for batch operations on multiple tasks.

This module provides reusable helpers for CLI commands that operate on multiple task IDs,
reducing code duplication and ensuring consistent error handling across commands.
"""

from collections.abc import Callable

from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
)
from presentation.console.console_writer import ConsoleWriter


def execute_batch_operation(  # noqa: C901
    task_ids: tuple[int, ...],
    operation: Callable[[int], None],
    console_writer: ConsoleWriter,
    operation_name: str,
) -> None:
    """Execute an operation on multiple tasks with consistent error handling.

    Args:
        task_ids: Tuple of task IDs to process
        operation: Function that takes a task_id and performs the operation
        console_writer: Console writer for output
        operation_name: Name of the operation (e.g., "starting task", "completing task")
    """
    for task_id in task_ids:
        try:
            operation(task_id)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.validation_error(
                f"Cannot {operation_name} task {e.task_id}: Task is already {e.status}."
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotStartedError as e:
            console_writer.validation_error(
                f"Cannot {operation_name} task {e.task_id}: Task is still PENDING. "
                f"Start the task first with: taskdog start {e.task_id}"
            )
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error(operation_name, e)
            if len(task_ids) > 1:
                console_writer.empty_line()
