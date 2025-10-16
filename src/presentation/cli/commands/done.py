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


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):  # noqa: C901
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)

    for task_id in task_ids:
        try:
            input_dto = CompleteTaskInput(task_id=task_id)
            task = complete_task_use_case.execute(input_dto)

            # Print success message
            console_writer.print_success("Completed", task)

            # Show completion time and duration if available
            if task.actual_end:
                console_writer.print(f"  Completed at: [blue]{task.actual_end}[/blue]")

            if task.actual_duration_hours:
                console_writer.print(f"  Duration: [cyan]{task.actual_duration_hours}h[/cyan]")

                # Show comparison with estimate if available
                if task.estimated_duration:
                    diff = task.actual_duration_hours - task.estimated_duration
                    if diff > 0:
                        console_writer.print(
                            f"  [yellow]⚠[/yellow] Took [yellow]{
                                diff
                            }h longer[/yellow] than estimated"
                        )
                    elif diff < 0:
                        console_writer.print(
                            f"  [green]✓[/green] Finished [green]{
                                abs(diff)
                            }h faster[/green] than estimated"
                        )
                    else:
                        console_writer.print("  [green]✓[/green] Finished exactly on estimate!")

            # Add spacing between tasks if processing multiple
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotFoundException as e:
            console_writer.print_task_not_found_error(e.task_id)
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskAlreadyFinishedError as e:
            console_writer.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
            console_writer.print(f"  [yellow]⚠[/yellow] Task is already {e.status}")
            console_writer.print("  [dim]Task has already been completed.[/dim]")
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except TaskNotStartedError as e:
            console_writer.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
            console_writer.print(
                f"  [yellow]⚠[/yellow] Task is still PENDING. Start the task first with [blue]taskdog start {
                    e.task_id
                }[/blue]"
            )
            if len(task_ids) > 1:
                console_writer.print_empty_line()

        except Exception as e:
            console_writer.print_error("completing task", e)
            if len(task_ids) > 1:
                console_writer.print_empty_line()
