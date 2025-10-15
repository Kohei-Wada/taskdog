"""Done command - Mark a task as completed."""

import click

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.complete_task import CompleteTaskUseCase
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
)
from presentation.cli.context import CliContext
from utils.console_messages import print_error, print_success, print_task_not_found_error


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):  # noqa: C901
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)

    for task_id in task_ids:
        try:
            input_dto = CompleteTaskInput(task_id=task_id)
            task = complete_task_use_case.execute(input_dto)

            # Print success message
            print_success(console, "Completed", task)

            # Show completion time and duration if available
            if task.actual_end:
                console.print(f"  Completed at: [blue]{task.actual_end}[/blue]")

            if task.actual_duration_hours:
                console.print(f"  Duration: [cyan]{task.actual_duration_hours}h[/cyan]")

                # Show comparison with estimate if available
                if task.estimated_duration:
                    diff = task.actual_duration_hours - task.estimated_duration
                    if diff > 0:
                        console.print(
                            f"  [yellow]⚠[/yellow] Took [yellow]{
                                diff
                            }h longer[/yellow] than estimated"
                        )
                    elif diff < 0:
                        console.print(
                            f"  [green]✓[/green] Finished [green]{
                                abs(diff)
                            }h faster[/green] than estimated"
                        )
                    else:
                        console.print("  [green]✓[/green] Finished exactly on estimate!")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            if len(task_ids) > 1:
                console.print()

        except TaskAlreadyFinishedError as e:
            console.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
            console.print(f"  [yellow]⚠[/yellow] Task is already {e.status}")
            console.print("  [dim]Task has already been completed.[/dim]")
            if len(task_ids) > 1:
                console.print()

        except TaskNotStartedError as e:
            console.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
            console.print(
                f"  [yellow]⚠[/yellow] Task is still PENDING. Start the task first with [blue]taskdog start {
                    e.task_id
                }[/blue]"
            )
            if len(task_ids) > 1:
                console.print()

        except Exception as e:
            print_error(console, "completing task", e)
            if len(task_ids) > 1:
                console.print()
