"""Estimate command - Set estimated duration for a task."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from utils.console_messages import print_update_success


@click.command(name="estimate", help="Set estimated duration for a task.")
@click.argument("task_id", type=int)
@click.argument("hours", type=float)
@click.pass_context
@handle_task_errors("setting estimate")
def estimate_command(ctx, task_id, hours):
    """Set estimated duration for a task.

    Usage:
        taskdog estimate <TASK_ID> <HOURS>

    Examples:
        taskdog estimate 5 2.5
        taskdog estimate 10 8.0
    """
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, estimated_duration=hours)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    print_update_success(ctx_obj.console, task, "estimated duration", hours, lambda h: f"{h}h")
