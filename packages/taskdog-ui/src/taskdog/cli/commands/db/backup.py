"""`db backup` - Download a physical snapshot of the database."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext


@click.command(
    name="backup",
    help="Back up the database to a physical .db snapshot.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    help="Output file path (default: ./taskdog-backup-YYYYMMDD-HHMMSS.db).",
)
@click.pass_context
def backup_command(ctx: click.Context, output: str | None) -> None:
    """Download a consistent physical snapshot of the server database.

    Unlike `export` (logical JSON/CSV), this is a full physical snapshot
    intended for real recovery.

    Examples:
        taskdog db backup                       # save to ./taskdog-backup-<ts>.db
        taskdog db backup -o /backups/tasks.db  # save to a specific path
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    if output:
        path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = Path.cwd() / f"taskdog-backup-{timestamp}.db"

    try:
        api_client.backup(path)
        console_writer.success(f"Backup saved to {path}")
    except Exception as e:
        console_writer.error("backing up database", e)
        raise click.Abort() from e
