"""Archive command - Archive a task."""

import click

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.archive_task import ArchiveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from presentation.cli.context import CliContext
from utils.console_messages import print_error, print_task_not_found_error


@click.command(
    name="archive", help="Archive task(s) for data retention (hidden from views by default)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def archive_command(ctx, task_ids):
    """Archive task(s)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    archive_task_use_case = ArchiveTaskUseCase(repository)

    for task_id in task_ids:
        try:
            input_dto = ArchiveTaskInput(task_id=task_id)
            archive_task_use_case.execute(input_dto)

            console.print(f"[green]✓[/green] Archived task with ID: [cyan]{task_id}[/cyan]")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            if len(task_ids) > 1:
                console.print()

        except Exception as e:
            print_error(console, "archiving task", e)
            if len(task_ids) > 1:
                console.print()
