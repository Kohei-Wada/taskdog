"""Common error handling decorators for CLI commands."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

import click

from taskdog.cli.context import CliContext
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException

F = TypeVar("F", bound=Callable[..., Any])


def handle_task_errors(action_name: str) -> Callable[[F], F]:
    """Decorator for task-specific error handling in CLI commands.

    Use this for commands that operate on specific task IDs (add, update, remove).

    Args:
        action_name: Action description for error messages (e.g., "adding task", "starting task")

    Usage:
        @handle_task_errors("adding task")
        def add_command(ctx, ...):
            # Command logic

    This decorator catches:
    - TaskNotFoundException: Shows "Task {id} not found" error
    - General Exception: Shows formatted error with action context
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract console_writer from context
            ctx = click.get_current_context()
            ctx_obj: CliContext = ctx.obj
            console_writer = ctx_obj.console_writer

            try:
                return func(*args, **kwargs)
            except TaskNotFoundException as e:
                console_writer.validation_error(str(e))
            except Exception as e:
                console_writer.error(action_name, e)

        return cast(F, wrapper)

    return decorator


def handle_command_errors(action_name: str) -> Callable[[F], F]:
    """Decorator for general command error handling.

    Use this for commands that don't operate on specific task IDs (tree, table, gantt, today).
    Lighter weight than handle_task_errors - only catches general exceptions.

    Args:
        action_name: Action description for error messages (e.g., "displaying tasks")

    Usage:
        @handle_command_errors("displaying tasks")
        def tree_command(ctx, ...):
            # Command logic

    This decorator catches:
    - General Exception: Shows formatted error with action context
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract console_writer from context
            ctx = click.get_current_context()
            ctx_obj: CliContext = ctx.obj
            console_writer = ctx_obj.console_writer

            try:
                return func(*args, **kwargs)
            except Exception as e:
                console_writer.error(action_name, e)

        return cast(F, wrapper)

    return decorator
