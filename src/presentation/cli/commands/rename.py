"""Rename command - Rename a task."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors


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
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, name=name)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    ctx_obj.console_writer.print_update_success(task, "name", name)
