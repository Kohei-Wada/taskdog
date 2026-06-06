"""Database command group."""

from __future__ import annotations

from taskdog.cli.lazy_group import LazyGroup

db_group = LazyGroup(
    name="db",
    help="Back up and restore the database.",
    lazy_subcommands={
        "backup": (
            "taskdog.cli.commands.db.backup.backup_command",
            "Back up the database to a physical .db snapshot.",
        ),
        "restore": (
            "taskdog.cli.commands.db.restore.restore_command",
            "Restore the database from a physical .db snapshot (applied on restart).",
        ),
    },
)
