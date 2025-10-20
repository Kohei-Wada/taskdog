"""Rm command - Remove a task."""

import click

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext


@click.command(name="rm", help="Remove task(s) (soft delete by default, --hard for permanent).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--hard",
    is_flag=True,
    help="Permanently delete the task(s) instead of soft delete.",
)
@click.pass_context
def rm_command(ctx, task_ids, hard):
    """Remove task(s).

    By default, tasks are soft deleted (archived) and can be restored with 'taskdog restore'.
    Use --hard flag to permanently delete tasks from the database.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    for task_id in task_ids:
        try:
            if hard:
                # Hard delete: permanently remove from database
                input_dto = RemoveTaskInput(task_id=task_id)
                use_case = RemoveTaskUseCase(repository)
                use_case.execute(input_dto)
                console_writer.print_success(f"Permanently deleted task with ID: {task_id}")
            else:
                # Soft delete: archive (set is_deleted=True)
                input_dto = ArchiveTaskInput(task_id=task_id)
                use_case = ArchiveTaskUseCase(repository)
                task = use_case.execute(input_dto)
                console_writer.task_success("Archived", task)
                console_writer.info(f"Use 'taskdog restore {task_id}' to restore this task.")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.empty_line()

        except TaskNotFoundException as e:
            console_writer.validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.empty_line()

        except Exception as e:
            console_writer.error("removing task", e)
            if len(task_ids) > 1:
                console_writer.empty_line()
