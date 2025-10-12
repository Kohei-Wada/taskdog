"""Deadline command - Set task deadline."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from shared.click_types.datetime_with_default import DateTimeWithDefault
from utils.console_messages import print_update_success


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
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, deadline=deadline)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    print_update_success(ctx_obj.console, task, "deadline", deadline)
