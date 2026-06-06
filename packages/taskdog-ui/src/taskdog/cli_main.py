from typing import Any

import click
from rich.console import Console

from taskdog import __version__
from taskdog.cli.context import CliContext
from taskdog.cli.lazy_group import LazyGroup
from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog.infrastructure.cli_config_manager import load_cli_config

# Registry of every subcommand: name -> (import path "module.attr", summary).
#
# The summary is kept here as a static string so `taskdog --help` can list all
# commands WITHOUT importing them — importing a command drags in heavy deps
# (rich, markdown_it, pydantic DTOs, Textual for `tui`) and dominates startup.
# Each command module is imported only when that command is actually invoked.
# This mirrors pip's `commands_dict` registry. Noun subgroups (dep, tag, db,
# audit) are themselves lazy groups, so listing them imports nothing either.
LAZY_SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "add": ("taskdog.cli.commands.add.add_command", "Add a new task."),
    "audit": (
        "taskdog.cli.commands.audit.audit_group",
        "Inspect operation history (audit logs).",
    ),
    "cancel": (
        "taskdog.cli.commands.cancel.cancel_command",
        "Mark task(s) as canceled.",
    ),
    "db": (
        "taskdog.cli.commands.db.db_group",
        "Back up and restore the database.",
    ),
    "dep": (
        "taskdog.cli.commands.dep.dep_group",
        "Manage task dependencies.",
    ),
    "done": ("taskdog.cli.commands.done.done_command", "Mark task(s) as completed."),
    "export": (
        "taskdog.cli.commands.export.export_command",
        "Export tasks to various formats (exports non-archived tasks by default).",
    ),
    "fix-times": (
        "taskdog.cli.commands.fix_times.fix_times_command",
        "Correct actual start/end timestamps and duration for a task.",
    ),
    "gantt": (
        "taskdog.cli.commands.gantt.gantt_command",
        "Display tasks in Gantt chart format with workload analysis.",
    ),
    "list": (
        "taskdog.cli.commands.list.list_command",
        "Display tasks in flat table format (shows non-archived tasks by default).",
    ),
    "note": ("taskdog.cli.commands.note.note_command", "Edit task notes in markdown."),
    "optimize": (
        "taskdog.cli.commands.optimize.optimize_command",
        "Auto-generate optimal schedules for tasks based on priority, deadlines, and workload.",
    ),
    "pause": (
        "taskdog.cli.commands.pause.pause_command",
        "Pause task(s) and reset time tracking (sets status to PENDING).",
    ),
    "reopen": (
        "taskdog.cli.commands.reopen.reopen_command",
        "Reopen completed or canceled task(s).",
    ),
    "restore": (
        "taskdog.cli.commands.restore.restore_command",
        "Restore archived task(s).",
    ),
    "rm": (
        "taskdog.cli.commands.rm.rm_command",
        "Remove task(s) (archive by default, --hard for permanent deletion).",
    ),
    "show": (
        "taskdog.cli.commands.show.show_command",
        "Show task details and notes with markdown rendering.",
    ),
    "start": (
        "taskdog.cli.commands.start.start_command",
        "Start working on task(s) (sets status to IN_PROGRESS).",
    ),
    "stats": (
        "taskdog.cli.commands.stats.stats_command",
        "Display task statistics and analytics.",
    ),
    "tag": (
        "taskdog.cli.commands.tag.tag_group",
        "View, set, or delete task tags.",
    ),
    "timeline": (
        "taskdog.cli.commands.timeline.timeline_command",
        "Display actual work times for a specific day.",
    ),
    "update": (
        "taskdog.cli.commands.update.update_command",
        "Update multiple task properties at once.",
    ),
    "tui": (
        "taskdog.cli.commands.tui.tui_command",
        "Launch the Text User Interface for interactive task management.",
    ),
}

# Aliases: alias -> canonical command name (hidden from the command listing).
COMMAND_ALIASES: dict[str, str] = {"ls": "list"}


class TaskdogGroup(LazyGroup):
    """Root group: lazy loading (via LazyGroup) plus ASCII art in --help."""

    def format_help(self, ctx: click.Context, formatter: Any) -> None:
        """Override format_help to add ASCII art before help text."""
        from taskdog.constants.ascii_art import (
            TASKDOG_ASCII_ART,
            TASKDOG_DESCRIPTION,
            TASKDOG_TAGLINE,
        )

        console = Console()
        console.print(TASKDOG_ASCII_ART, style="cyan")
        console.print(f"  {TASKDOG_TAGLINE}", style="bold yellow")
        console.print(f"  {TASKDOG_DESCRIPTION}", style="dim")
        console.print()

        # Call the original format_help
        super().format_help(ctx, formatter)


@click.group(
    cls=TaskdogGroup,
    lazy_subcommands=LAZY_SUBCOMMANDS,
    aliases=COMMAND_ALIASES,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="taskdog")
@click.option(
    "-H",
    "--host",
    type=str,
    default=None,
    help="API server host (overrides config/env)",
)
@click.option(
    "-p",
    "--port",
    type=click.IntRange(1, 65535),
    default=None,
    help="API server port (overrides config/env)",
)
@click.option(
    "-k",
    "--api-key",
    type=str,
    default=None,
    help="API key for authentication (overrides config/env)",
)
@click.pass_context
def cli(
    ctx: click.Context, host: str | None, port: int | None, api_key: str | None
) -> None:
    """Taskdog: Task management CLI tool with time tracking and optimization."""
    # Display help when no subcommand is provided
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    # Initialize shared dependencies
    console = Console()
    console_writer = RichConsoleWriter(console)
    config = load_cli_config()

    # CLI options override config/env settings
    api_host = host if host is not None else config.api.host
    api_port = port if port is not None else config.api.port
    effective_api_key = api_key if api_key is not None else config.api.api_key

    # Initialize API client (required for all CLI commands)
    # Health check is deferred to actual API calls for better performance
    from taskdog_client import TaskdogApiClient

    api_client = TaskdogApiClient(
        base_url=f"http://{api_host}:{api_port}",
        api_key=effective_api_key,
    )

    # Store in CliContext for type-safe access
    ctx.ensure_object(dict)
    ctx.obj = CliContext(
        console_writer=console_writer,
        api_client=api_client,
        config=config,
    )


if __name__ == "__main__":
    cli()
