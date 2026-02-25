"""Helper functions for batch operations on multiple tasks.

This module provides reusable helpers for CLI commands that operate on multiple task IDs,
reducing code duplication and ensuring consistent error handling across commands.
"""

from collections.abc import Callable

from taskdog.console.console_writer import ConsoleWriter
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


def _add_spacing_if_batch(
    task_ids: tuple[int, ...], console_writer: ConsoleWriter
) -> None:
    """Add empty line spacing if processing multiple tasks.

    Args:
        task_ids: Tuple of task IDs being processed
        console_writer: Console writer for output
    """
    if len(task_ids) > 1:
        console_writer.empty_line()


def execute_batch_operation(
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
            _add_spacing_if_batch(task_ids, console_writer)

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            _add_spacing_if_batch(task_ids, console_writer)

        except TaskValidationError as e:
            console_writer.validation_error(str(e))
            _add_spacing_if_batch(task_ids, console_writer)

        except Exception as e:
            console_writer.error(operation_name, e)
            _add_spacing_if_batch(task_ids, console_writer)
