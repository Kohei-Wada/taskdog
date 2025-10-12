"""Update command - Update task properties."""

import click
from domain.entities.task import TaskStatus
from domain.services.time_tracker import TimeTracker
from shared.click_types.datetime_with_default import DateTimeWithDefault
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.error_handler import handle_task_errors


@click.command(
    name="update", help="Update task properties (priority, status, dates, duration)."
)
@click.option(
    "--id",
    "task_id",
    type=int,
    prompt="Task ID",
    help="The ID of the task to update.",
)
@click.option(
    "--priority",
    type=int,
    default=None,
    help="New priority",
)
@click.option(
    "--status",
    type=click.Choice([e.value for e in TaskStatus]),
    default=None,
    help="New status",
)
@click.option(
    "--planned-start",
    type=DateTimeWithDefault(),
    default=None,
    help="Planned start (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--planned-end",
    type=DateTimeWithDefault(),
    default=None,
    help="Planned end (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--deadline",
    type=DateTimeWithDefault(),
    default=None,
    help="Deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, defaults to 18:00:00)",
)
@click.option(
    "--estimated-duration",
    type=float,
    default=None,
    help="Estimated duration in hours (e.g., 2.5)",
)
@click.pass_context
@handle_task_errors("updating task")
def update_command(
    ctx,
    task_id,
    priority,
    status,
    planned_start,
    planned_end,
    deadline,
    estimated_duration,
):
    """Update task properties."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Convert status string to Enum if provided
    status_enum = TaskStatus(status) if status else None

    # Build input DTO
    input_dto = UpdateTaskInput(
        task_id=task_id,
        priority=priority,
        status=status_enum,
        planned_start=planned_start,
        planned_end=planned_end,
        deadline=deadline,
        estimated_duration=estimated_duration,
    )

    # Execute use case
    task, updated_fields = update_task_use_case.execute(input_dto)

    if not updated_fields:
        console.print(
            "[yellow]No fields to update.[/yellow] Use --priority, --status, --planned-start, --planned-end, --deadline, or --estimated-duration"
        )
        return

    # Print updates
    console.print(
        f"[green]✓[/green] Updated task [bold]{task.name}[/bold] (ID: [cyan]{
            task.id
        }[/cyan]):"
    )
    for field in updated_fields:
        value = getattr(task, field)
        if field == "estimated_duration":
            console.print(f"  • {field}: [cyan]{value}h[/cyan]")
        else:
            console.print(f"  • {field}: [cyan]{value}[/cyan]")
