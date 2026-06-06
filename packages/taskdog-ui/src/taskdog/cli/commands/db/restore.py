"""`db restore` - Upload a database snapshot to be applied on restart."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from taskdog.cli.context import CliContext


@click.command(
    name="restore",
    help="Restore the database from a physical .db snapshot (applied on restart).",
)
@click.argument(
    "file_path",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip the confirmation prompt.",
)
@click.pass_context
def restore_command(ctx: click.Context, file_path: str, yes: bool) -> None:
    """Upload a `.db` snapshot to replace the server database.

    This is destructive: the snapshot is staged now and replaces the live
    database the next time the server starts. Restart the server to apply.

    Examples:
        taskdog db restore ./taskdog-backup-20250101-120000.db
        taskdog db restore backup.db --yes
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    if not yes and not click.confirm(
        f"This will replace the server database with '{file_path}' on the next "
        "server restart. Continue?"
    ):
        console_writer.info("Restore canceled.")
        return

    try:
        result = api_client.restore(Path(file_path))
        console_writer.success(
            f"Restore staged ({result.status}). Restart the server to apply."
        )
    except Exception as e:
        console_writer.error("restoring database", e)
        raise click.Abort() from e
