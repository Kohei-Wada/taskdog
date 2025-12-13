"""Fix-actual command - Correct actual start/end timestamps and duration."""

from datetime import datetime
from typing import Any

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault

# Sentinel value for "clear" - distinct from None (not provided)
CLEAR_SENTINEL = "CLEAR"


class ClearableDateTimeType(click.ParamType):
    """DateTime type that treats empty string as 'clear' command."""

    name = "DATETIME"

    def __init__(self, default_hour: int | str | None = None) -> None:
        """Initialize with wrapped DateTimeWithDefault.

        Args:
            default_hour: Hour to use when only date provided.
                         None = end hour (18:00), "start" = start hour (9:00)
        """
        self._inner = DateTimeWithDefault(default_hour)

    def convert(
        self, value: Any, param: Any, ctx: click.Context | None
    ) -> datetime | str | None:
        """Convert value, treating empty string as clear sentinel."""
        if value == "" or value == CLEAR_SENTINEL:
            return CLEAR_SENTINEL
        return self._inner.convert(value, param, ctx)


class ClearableFloatType(click.ParamType):
    """Float type that treats empty string as 'clear' command."""

    name = "FLOAT"

    def convert(self, value: Any, param: Any, ctx: click.Context | None) -> float | str:
        """Convert value, treating empty string as clear sentinel."""
        if value == "" or value == CLEAR_SENTINEL:
            return CLEAR_SENTINEL
        try:
            return float(value)
        except ValueError:
            self.fail(f"{value!r} is not a valid float", param, ctx)


@click.command(
    name="fix-actual",
    help="Correct actual start/end timestamps and duration for a task.",
)
@click.argument("task_id", type=int)
@click.option(
    "--start",
    "-s",
    type=ClearableDateTimeType("start"),
    default=None,
    help='Actual start datetime (empty string "" to clear)',
)
@click.option(
    "--end",
    "-e",
    type=ClearableDateTimeType(),
    default=None,
    help='Actual end datetime (empty string "" to clear)',
)
@click.option(
    "--duration",
    "-d",
    type=ClearableFloatType(),
    default=None,
    help='Actual duration in hours (empty string "" to clear)',
)
@click.pass_context
@handle_task_errors("fixing actual times")
def fix_actual_command(
    ctx: click.Context,
    task_id: int,
    start: datetime | str | None,
    end: datetime | str | None,
    duration: float | str | None,
) -> None:
    """Correct actual start/end timestamps and/or duration for a task.

    Used to fix timestamps for historical accuracy. Past dates are allowed.
    The --duration option allows setting explicit work hours when the calculated
    duration from timestamps doesn't reflect actual work (e.g., multi-day tasks).

    Use empty string "" to clear a value.

    Examples:
        taskdog fix-actual 5 --start "2025-12-13T09:00:00"
        taskdog fix-actual 5 --start "2025-12-13T09:00:00" --end "2025-12-13T17:00:00"
        taskdog fix-actual 5 --duration 8
        taskdog fix-actual 5 --start "2025-12-01" --end "2025-12-03" --duration 16
        taskdog fix-actual 5 --start ""      # Clear actual_start
        taskdog fix-actual 5 --duration ""   # Clear actual_duration
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Determine clear flags
    clear_start = start == CLEAR_SENTINEL
    clear_end = end == CLEAR_SENTINEL
    clear_duration = duration == CLEAR_SENTINEL

    # Convert sentinels to None for actual values
    actual_start: datetime | None = (
        None if clear_start or start is None else start  # type: ignore[assignment]
    )
    actual_end: datetime | None = (
        None if clear_end or end is None else end  # type: ignore[assignment]
    )
    actual_duration: float | None = (
        None if clear_duration or duration is None else duration  # type: ignore[assignment]
    )

    # At least one option must be specified
    if (
        actual_start is None
        and actual_end is None
        and actual_duration is None
        and not clear_start
        and not clear_end
        and not clear_duration
    ):
        console_writer.validation_error(
            "At least one of --start, --end, or --duration is required"
        )
        ctx.exit(1)

    # Validate that end is not before start when both are provided
    if (
        actual_start is not None
        and actual_end is not None
        and actual_end < actual_start
    ):
        console_writer.validation_error(
            f"End time ({actual_end}) cannot be before start time ({actual_start})"
        )
        ctx.exit(1)

    # Validate duration is positive
    if actual_duration is not None and actual_duration <= 0:
        console_writer.validation_error("Duration must be greater than 0")
        ctx.exit(1)

    # Call API
    ctx_obj.api_client.fix_actual_times(
        task_id=task_id,
        actual_start=actual_start,
        actual_end=actual_end,
        actual_duration=actual_duration,
        clear_start=clear_start,
        clear_end=clear_end,
        clear_duration=clear_duration,
    )

    # Format output
    changes = []
    if actual_start is not None or clear_start:
        val = "cleared" if clear_start else str(actual_start)
        changes.append(f"actual_start: {val}")
    if actual_end is not None or clear_end:
        val = "cleared" if clear_end else str(actual_end)
        changes.append(f"actual_end: {val}")
    if actual_duration is not None or clear_duration:
        val = "cleared" if clear_duration else f"{actual_duration}h"
        changes.append(f"actual_duration: {val}")

    console_writer.success(
        f"Fixed actual times for task {task_id}: {', '.join(changes)}"
    )
