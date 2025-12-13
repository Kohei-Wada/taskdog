"""Fix-actual command - Correct actual start/end timestamps."""

from datetime import datetime

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(
    name="fix-actual", help="Correct actual start/end timestamps for a task."
)
@click.argument("task_id", type=int)
@click.option(
    "--start",
    "-s",
    type=DateTimeWithDefault("start"),
    default=None,
    help="New actual start datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--end",
    "-e",
    type=DateTimeWithDefault(),
    default=None,
    help="New actual end datetime (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--clear-start",
    is_flag=True,
    default=False,
    help="Clear actual_start timestamp",
)
@click.option(
    "--clear-end",
    is_flag=True,
    default=False,
    help="Clear actual_end timestamp",
)
@click.pass_context
@handle_task_errors("fixing actual times")
def fix_actual_command(
    ctx: click.Context,
    task_id: int,
    start: datetime | None,
    end: datetime | None,
    clear_start: bool,
    clear_end: bool,
) -> None:
    """Correct actual start/end timestamps for a task.

    Used to fix timestamps for historical accuracy. Past dates are allowed.

    Examples:
        taskdog fix-actual 5 --start "2025-12-13T09:00:00"
        taskdog fix-actual 5 --start "2025-12-13T09:00:00" --end "2025-12-13T17:00:00"
        taskdog fix-actual 5 --clear-start
        taskdog fix-actual 5 --clear-start --clear-end
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Validate mutually exclusive options
    if start is not None and clear_start:
        console_writer.validation_error("Cannot use --start and --clear-start together")
        ctx.exit(1)
    if end is not None and clear_end:
        console_writer.validation_error("Cannot use --end and --clear-end together")
        ctx.exit(1)

    # At least one option must be specified
    if start is None and end is None and not clear_start and not clear_end:
        console_writer.validation_error(
            "At least one of --start, --end, --clear-start, or --clear-end is required"
        )
        ctx.exit(1)

    # Validate that end is not before start when both are provided
    if start is not None and end is not None and end < start:
        console_writer.validation_error(
            f"End time ({end}) cannot be before start time ({start})"
        )
        ctx.exit(1)

    # Call API
    ctx_obj.api_client.fix_actual_times(
        task_id=task_id,
        actual_start=start,
        actual_end=end,
        clear_start=clear_start,
        clear_end=clear_end,
    )

    # Format output
    changes = []
    if start is not None or clear_start:
        val = "cleared" if clear_start else str(start)
        changes.append(f"actual_start: {val}")
    if end is not None or clear_end:
        val = "cleared" if clear_end else str(end)
        changes.append(f"actual_end: {val}")

    console_writer.success(
        f"Fixed actual times for task {task_id}: {', '.join(changes)}"
    )
