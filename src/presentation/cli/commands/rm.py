"""Rm command - Remove a task."""

import click

from application.dto.archive_task_request import ArchiveTaskRequest
from application.dto.remove_task_request import RemoveTaskRequest
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(
    name="rm", help="Remove task(s) (archive by default, --hard for permanent deletion)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--hard",
    is_flag=True,
    help="Permanently delete the task(s) instead of archiving.",
)
@click.pass_context
def rm_command(ctx, task_ids, hard):
    """Remove task(s).

    By default, tasks are archived (status changed to ARCHIVED) and can be restored with 'taskdog restore'.
    Tasks can be archived from any status (soft delete).
    Use --hard flag to permanently delete tasks from the database.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    def remove_single_task(task_id: int) -> None:
        if hard:
            # Hard delete: permanently remove from database
            input_dto = RemoveTaskRequest(task_id=task_id)
            use_case = RemoveTaskUseCase(repository)
            use_case.execute(input_dto)
            console_writer.success(f"Permanently deleted task with ID: {task_id}")
        else:
            # Archive: change status to ARCHIVED
            input_dto = ArchiveTaskRequest(task_id=task_id)
            use_case = ArchiveTaskUseCase(repository, ctx_obj.time_tracker)
            task = use_case.execute(input_dto)
            console_writer.task_success(StatusVerbs.ARCHIVED, task)
            console_writer.info(f"Use 'taskdog restore {task_id}' to restore this task.")

    execute_batch_operation(task_ids, remove_single_task, console_writer, "removing task")
