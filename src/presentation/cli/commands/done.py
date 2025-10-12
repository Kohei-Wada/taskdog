"""Done command - Mark a task as completed."""

import click

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.complete_task import CompleteTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import IncompleteChildrenError, TaskNotFoundException
from domain.services.time_tracker import TimeTracker
from utils.console_messages import print_error, print_success, print_task_not_found_error


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):
    """Mark task(s) as completed."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)

    success_count = 0
    error_count = 0

    for task_id in task_ids:
        try:
            input_dto = CompleteTaskInput(task_id=task_id)
            task = complete_task_use_case.execute(input_dto)

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
                            f"  [yellow]⚠[/yellow] Took [yellow]{diff}h longer[/yellow] than estimated"
                        )
                    elif diff < 0:
                        console.print(
                            f"  [green]✓[/green] Finished [green]{abs(diff)}h faster[/green] than estimated"
                        )
                    else:
                        console.print("  [green]✓[/green] Finished exactly on estimate!")

            success_count += 1

            # Add spacing between multiple tasks
            if len(task_ids) > 1:
                console.print()

        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
            error_count += 1
            if len(task_ids) > 1:
                console.print()
        except IncompleteChildrenError as e:
            console.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
            console.print("  [yellow]⚠[/yellow] The following child tasks are not completed:")
            for child in e.incomplete_children:
                status_color = "blue" if child.status == TaskStatus.IN_PROGRESS else "yellow"
                console.print(
                    f"    - Task {child.id}: {child.name} ([{status_color}]{child.status.value}[/{status_color}])"
                )
            console.print("  [dim]Complete all child tasks first, then try again.[/dim]")
            error_count += 1
            if len(task_ids) > 1:
                console.print()
        except Exception as e:
            print_error(console, "completing task", e)
            error_count += 1
            if len(task_ids) > 1:
                console.print()

    # Show summary if multiple tasks were processed
    if len(task_ids) > 1:
        if success_count > 0 and error_count == 0:
            console.print(f"[green]✓[/green] Successfully completed {success_count} task(s)")
        elif success_count > 0 and error_count > 0:
            console.print(
                f"[yellow]⚠[/yellow] Completed {success_count} task(s), {error_count} error(s)"
            )
        elif error_count > 0:
            console.print(f"[red]✗[/red] Failed to complete {error_count} task(s)")
