"""Common error handling decorators for CLI commands."""

from functools import wraps

import click

from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext


def handle_task_errors(action_name: str, is_parent: bool = False):
    """Decorator for task-specific error handling in CLI commands.

    Use this for commands that operate on specific task IDs (add, update, remove).

    Args:
        action_name: Action description for error messages (e.g., "adding task", "starting task")
        is_parent: Whether this is a parent task error (default: False)

    Usage:
        @handle_task_errors("adding task", is_parent=True)
        def add_command(ctx, ...):
            # Command logic

    This decorator catches:
    - TaskNotFoundException: Shows "Task {id} not found" error
    - General Exception: Shows formatted error with action context
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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

        return wrapper

    return decorator


def handle_command_errors(action_name: str):
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

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract console_writer from context
            ctx = click.get_current_context()
            ctx_obj: CliContext = ctx.obj
            console_writer = ctx_obj.console_writer

            try:
                return func(*args, **kwargs)
            except Exception as e:
                console_writer.error(action_name, e)

        return wrapper

    return decorator
