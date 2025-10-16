"""Start command - Start working on a task."""

import click

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from presentation.cli.context import CliContext


@click.command(name="start", help="Start working on task(s) (sets status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):  # noqa: C901
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    start_task_use_case = StartTaskUseCase(repository, time_tracker)

    for task_id in task_ids:
        try:
            # Check current status before starting
            task_before = repository.get_by_id(task_id)
            was_already_in_progress = task_before and task_before.status == TaskStatus.IN_PROGRESS

            input_dto = StartTaskInput(task_id=task_id)
            task = start_task_use_case.execute(input_dto)

            # Print success message
            console_writer.print_success("Started", task)

            if was_already_in_progress:
                console_writer.print(
                    f"  [yellow]⚠[/yellow] Task was already IN_PROGRESS (started at [blue]{
                        task.actual_start
                    }[/blue])"
                )
            elif task.actual_start:
                console_writer.print(f"  Started at: [blue]{task.actual_start}[/blue]")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotFoundException as e:
            console_writer.print_task_not_found_error(e.task_id)
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.print(f"[red]✗[/red] Cannot start task {e.task_id}")
            console_writer.print(f"  [yellow]⚠[/yellow] Task is already {e.status}")
            console_writer.print("  [dim]Finished tasks cannot be restarted.[/dim]")
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except Exception as e:
            console_writer.print_error("starting task", e)
            if len(task_ids) > 1:
                console_writer.print_empty_line()
