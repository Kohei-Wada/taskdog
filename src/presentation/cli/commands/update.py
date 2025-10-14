"""Update command - Update task properties."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.constants import DEFAULT_START_HOUR
from domain.entities.task import TaskStatus
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(
    name="update",
    help="Update multiple task properties at once. For single-field updates, prefer specialized commands (deadline, priority, rename, estimate, schedule).",
)
@click.argument("task_id", type=int)
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
    type=DateTimeWithDefault(default_hour=DEFAULT_START_HOUR),
    default=None,
    help="Planned start (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 09:00:00)",
)
@click.option(
    "--planned-end",
    type=DateTimeWithDefault(),
    default=None,
    help="Planned end (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 18:00:00)",
)
@click.option(
    "--deadline",
    type=DateTimeWithDefault(),
    default=None,
    help="Deadline (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 18:00:00)",
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
    """Update multiple task properties at once.

    Usage:
        taskdog update <TASK_ID> [OPTIONS]

    Examples:
        # Update multiple fields at once
        taskdog update 5 --priority 3 --deadline 2025-10-15

        # Update status and record time
        taskdog update 10 --status IN_PROGRESS

        # Update deadline and estimated duration
        taskdog update 7 --deadline 2025-10-20 --estimated-duration 4.0

    For single-field updates, prefer specialized commands:
        taskdog deadline <ID> <DATE>
        taskdog priority <ID> <PRIORITY>
        taskdog estimate <ID> <HOURS>
        taskdog schedule <ID> <START> [END]
    """
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
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
        f"[green]✓[/green] Updated task [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]):"
    )
    for field in updated_fields:
        value = getattr(task, field)
        if field == "estimated_duration":
            console.print(f"  • {field}: [cyan]{value}h[/cyan]")
        else:
            console.print(f"  • {field}: [cyan]{value}[/cyan]")
