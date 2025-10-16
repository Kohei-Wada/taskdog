"""Archive command - Archive a task."""

import click

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext


@click.command(
    name="archive", help="Archive task(s) for data retention (hidden from views by default)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def archive_command(ctx, task_ids):
    """Archive task(s)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    archive_task_use_case = ArchiveTaskUseCase(repository)

    for task_id in task_ids:
        try:
            input_dto = ArchiveTaskInput(task_id=task_id)
            archive_task_use_case.execute(input_dto)

            console_writer.print_task_archived(task_id)

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotFoundException as e:
            console_writer.print_validation_error(str(e))
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except Exception as e:
            console_writer.print_error("archiving task", e)
            if len(task_ids) > 1:
                console_writer.print_empty_line()
