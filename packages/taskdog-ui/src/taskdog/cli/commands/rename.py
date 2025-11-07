"""Rename command - Rename a task."""

import click

from taskdog.cli.commands.update_helpers import execute_single_field_update
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors


@click.command(name="rename", help="Rename a task.")
@click.argument("task_id", type=int)
@click.argument("name", type=str)
@click.pass_context
@handle_task_errors("renaming task")
def rename_command(ctx, task_id, name):
    """Rename a task.

    Usage:
        taskdog rename <TASK_ID> <NEW_NAME>

    Examples:
        taskdog rename 5 "Implement authentication"
        taskdog rename 10 "Fix bug in login form"
    """
    task = execute_single_field_update(ctx, task_id, "name", name)
    ctx_obj: CliContext = ctx.obj
    ctx_obj.console_writer.update_success(task, "name", name)
