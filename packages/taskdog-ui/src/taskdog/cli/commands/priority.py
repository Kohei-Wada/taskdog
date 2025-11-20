"""Priority command - Set task priority."""

import click

from taskdog.cli.commands.update_helpers import execute_single_field_update
from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types import PositiveInt


@click.command(name="priority", help="Set task priority.")
@click.argument("task_id", type=int)
@click.argument("priority", type=PositiveInt())
@click.pass_context
@handle_task_errors("setting priority")
def priority_command(ctx: click.Context, task_id: int, priority: int) -> None:
    """Set priority for a task.

    Usage:
        taskdog priority <TASK_ID> <PRIORITY>

    Examples:
        taskdog priority 5 3
        taskdog priority 10 1
    """
    task = execute_single_field_update(ctx, task_id, "priority", priority)
    ctx_obj: CliContext = ctx.obj
    ctx_obj.console_writer.update_success(task, "priority", priority)
