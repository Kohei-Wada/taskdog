"""Priority command - Set task priority."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from utils.console_messages import print_update_success


@click.command(name="priority", help="Set task priority.")
@click.argument("task_id", type=int)
@click.argument("priority", type=int)
@click.pass_context
@handle_task_errors("setting priority")
def priority_command(ctx, task_id, priority):
    """Set priority for a task.

    Usage:
        taskdog priority <TASK_ID> <PRIORITY>

    Examples:
        taskdog priority 5 3
        taskdog priority 10 1
    """
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, priority=priority)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    print_update_success(ctx_obj.console, task, "priority", priority)
