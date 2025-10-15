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
from utils.console_messages import print_error, print_success, print_task_not_found_error


@click.command(name="start", help="Start working on task(s) (sets status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):  # noqa: C901
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
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
            print_success(console, "Started", task)

            if was_already_in_progress:
                console.print(
                    f"  [yellow]⚠[/yellow] Task was already IN_PROGRESS (started at [blue]{
                        task.actual_start
                    }[/blue])"
                )
            elif task.actual_start:
                console.print(f"  Started at: [blue]{task.actual_start}[/blue]")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            if len(task_ids) > 1:
                console.print()

        except TaskAlreadyFinishedError as e:
            console.print(f"[red]✗[/red] Cannot start task {e.task_id}")
            console.print(f"  [yellow]⚠[/yellow] Task is already {e.status}")
            console.print("  [dim]Finished tasks cannot be restarted.[/dim]")
            if len(task_ids) > 1:
                console.print()

        except Exception as e:
            print_error(console, "starting task", e)
            if len(task_ids) > 1:
                console.print()
