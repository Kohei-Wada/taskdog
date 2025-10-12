"""Plan command - Set planning details for a task."""

import click
from shared.click_types.datetime_with_default import DateTimeWithDefault
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.services.time_tracker import TimeTracker
from presentation.cli.error_handler import handle_task_errors


@click.command(
    name="plan", help="Set planning details for a task (duration, start, end)."
)
@click.argument("task_id", type=int)
@click.argument("estimated_duration", type=float)
@click.argument(
    "planned_start",
    type=DateTimeWithDefault(),
    required=False,
)
@click.argument(
    "planned_end",
    type=DateTimeWithDefault(),
    required=False,
)
@click.pass_context
@handle_task_errors("planning task")
def plan_command(ctx, task_id, estimated_duration, planned_start, planned_end):
    """Set planning details for a task with positional arguments.

    Usage:
        taskdog plan <ID> <DURATION>
        taskdog plan <ID> <DURATION> <START>
        taskdog plan <ID> <DURATION> <START> <END>

    Examples:
        taskdog plan 5 2.5
        taskdog plan 5 2.5 2025-10-15
        taskdog plan 5 2.5 2025-10-15 2025-10-17
        taskdog plan 5 2.5 "2025-10-15 09:00:00" "2025-10-15 17:00:00"
    """
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(
        task_id=task_id,
        estimated_duration=estimated_duration,
        planned_start=planned_start,
        planned_end=planned_end,
    )

    # Execute use case
    task, updated_fields = update_task_use_case.execute(input_dto)

    # Print updates
    console.print(
        f"[green]✓[/green] Planned task [bold]{task.name}[/bold] (ID: [cyan]{
            task.id
        }[/cyan]):"
    )
    for field in updated_fields:
        value = getattr(task, field)
        if field == "estimated_duration":
            console.print(f"  • {field}: [cyan]{value}h[/cyan]")
        else:
            console.print(f"  • {field}: [cyan]{value}[/cyan]")
