"""Deadline command - Set task deadline."""

import click

from taskdog.cli.commands.update_helpers import execute_single_field_update
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(name="deadline", help="Set task deadline.")
@click.argument("task_id", type=int)
@click.argument("deadline", type=DateTimeWithDefault())
@click.pass_context
@handle_task_errors("setting deadline")
def deadline_command(ctx, task_id, deadline):
    """Set deadline for a task.

    Usage:
        taskdog deadline <TASK_ID> <DATE>

    Date formats: YYYY-MM-DD, MM-DD, or MM/DD (defaults to 18:00:00)

    Examples:
        taskdog deadline 5 10-10
        taskdog deadline 5 2025-10-10
        taskdog deadline 5 "2025-10-10 18:00:00"
    """
    task = execute_single_field_update(ctx, task_id, "deadline", deadline)
    ctx_obj: CliContext = ctx.obj
    ctx_obj.console_writer.update_success(task, "deadline", deadline)
