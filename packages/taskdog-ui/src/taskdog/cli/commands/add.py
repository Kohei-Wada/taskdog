"""Add command - Add a new task."""

from datetime import datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


@click.command(name="add", help="Add a new task.")
@click.argument("name", type=str)
@click.option(
    "--priority",
    "-p",
    type=int,
    default=None,
    help="Task priority (default: from config or 5, higher value = higher priority)",
)
@click.option(
    "--fixed",
    "-f",
    is_flag=True,
    help="Mark task as fixed (won't be rescheduled by optimizer)",
)
@click.option(
    "--depends-on",
    "-d",
    multiple=True,
    type=int,
    help="Task IDs this task depends on (can be specified multiple times)",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Tags for categorization and filtering (can be specified multiple times)",
)
@click.option(
    "--deadline",
    "-D",
    type=DateTimeWithDefault(),
    default=None,
    help="Task deadline (formats: YYYY-MM-DD, MM-DD, YYYY-MM-DD HH:MM:SS)",
)
@click.option(
    "--estimate",
    "-e",
    type=float,
    default=None,
    help="Estimated duration in hours (must be > 0)",
)
@click.option(
    "--start",
    "-s",
    type=DateTimeWithDefault(default_hour="start"),
    default=None,
    help="Planned start time (formats: YYYY-MM-DD, MM-DD, YYYY-MM-DD HH:MM:SS)",
)
@click.option(
    "--end",
    "-E",
    type=DateTimeWithDefault(),
    default=None,
    help="Planned end time (formats: YYYY-MM-DD, MM-DD, YYYY-MM-DD HH:MM:SS)",
)
@click.pass_context
@handle_task_errors("adding task", is_parent=True)
def add_command(
    ctx: click.Context,
    name: str,
    priority: int,
    fixed: bool,
    depends_on: tuple[int, ...],
    tag: tuple[str, ...],
    deadline: datetime | None,
    estimate: float | None,
    start: datetime | None,
    end: datetime | None,
) -> None:
    """Add a new task.

    You can set all task properties at creation time, or use dedicated commands
    after creation (deadline, estimate, schedule) for updates.

    Usage:
        # Basic task
        taskdog add "Task name"

        # With priority and tags
        taskdog add "Task name" --priority 3 --tag backend

        # Full task with all properties
        taskdog add "Implement auth" -p 5 -D "2025-12-01" -e 8 -s "2025-11-20" -t backend

    Examples:
        # Simple task
        taskdog add "Implement authentication"

        # With priority
        taskdog add "Fix login bug" -p 5

        # With deadline and estimate
        taskdog add "Add unit tests" --deadline "2025-12-15" --estimate 4

        # Complete task with schedule
        taskdog add "Code review" -p 3 -s "2025-11-20 09:00" -e "2025-11-20 12:00"

        # With dependencies and tags
        taskdog add "Deploy feature" -d 123 -t deployment -p 5
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Create task via API client
    task = ctx_obj.api_client.create_task(
        name=name,
        priority=priority,
        is_fixed=fixed,
        tags=list(tag) if tag else None,
        deadline=deadline,
        estimated_duration=estimate,
        planned_start=start,
        planned_end=end,
    )

    # Add dependencies if specified
    if depends_on:
        for dep_id in depends_on:
            try:
                task = ctx_obj.api_client.add_dependency(task.id, dep_id)
            except TaskValidationError as e:
                console_writer.validation_error(str(e))
                # Continue adding other dependencies even if one fails

    console_writer.task_success("Added", task)
    if task.depends_on:
        console_writer.info(f"Dependencies: {task.depends_on}")
    if task.tags:
        console_writer.info(f"Tags: {', '.join(task.tags)}")
