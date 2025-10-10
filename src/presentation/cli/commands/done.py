"""Done command - Mark a task as completed."""

import click
from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_success, print_task_not_found_error, print_error
from application.dto.complete_task_input import CompleteTaskInput


@click.command(name="done", help="Mark a task as completed.")
@click.argument("task_id", type=int)
@click.pass_context
def done_command(ctx, task_id):
    """Mark a task as completed."""
    console = ctx.obj["console"]
    complete_task_use_case = ctx.obj["complete_task_use_case"]

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
                    console.print(f"  [green]✓[/green] Finished exactly on estimate!")

    except TaskNotFoundException as e:
        print_task_not_found_error(console, e.task_id)
    except Exception as e:
        print_error(console, "completing task", e)
