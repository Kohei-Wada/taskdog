import importlib
from typing import Any

import click
from rich.console import Console

from taskdog import __version__
from taskdog.cli.context import CliContext
from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog.infrastructure.cli_config_manager import load_cli_config

# Registry of every subcommand: name -> (import path "module.attr", summary).
#
# The summary is kept here as a static string so `taskdog --help` can list all
# commands WITHOUT importing them — importing a command drags in heavy deps
# (rich, markdown_it, pydantic DTOs, Textual for `tui`) and dominates startup.
# Each command module is imported only when that command is actually invoked.
# This mirrors pip's `commands_dict` registry.
LAZY_SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "add": ("taskdog.cli.commands.add.add_command", "Add a new task."),
    "add-dependency": (
        "taskdog.cli.commands.add_dependency.add_dependency_command",
        "Add a dependency to a task.",
    ),
    "audit-logs": (
        "taskdog.cli.commands.audit_logs.audit_logs_command",
        "Display operation history (audit logs).",
    ),
    "cancel": (
        "taskdog.cli.commands.cancel.cancel_command",
        "Mark task(s) as canceled.",
    ),
    "done": ("taskdog.cli.commands.done.done_command", "Mark task(s) as completed."),
    "export": (
        "taskdog.cli.commands.export.export_command",
        "Export tasks to various formats (exports non-archived tasks by default).",
    ),
    "fix-actual": (
        "taskdog.cli.commands.fix_actual.fix_actual_command",
        "Correct actual start/end timestamps and duration for a task.",
    ),
    "gantt": (
        "taskdog.cli.commands.gantt.gantt_command",
        "Display tasks in Gantt chart format with workload analysis.",
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
    "remove-dependency": (
        "taskdog.cli.commands.remove_dependency.remove_dependency_command",
        "Remove a dependency from a task.",
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
    "table": (
        "taskdog.cli.commands.table.table_command",
        "Display tasks in flat table format (shows non-archived tasks by default).",
    ),
    "tags": (
        "taskdog.cli.commands.tags.tags_command",
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


class TaskdogGroup(click.Group):
    """Custom Click Group with lazy loading and ASCII art help display.

    Implements Click's LazyGroup pattern (see
    https://click.palletsprojects.com/en/stable/complex/) so that no subcommand
    module is imported until the command is actually invoked. ``--help`` lists
    commands from the static summaries in ``LAZY_SUBCOMMANDS`` instead of
    importing them, keeping startup fast.
    """

    def __init__(
        self,
        *args: Any,
        lazy_subcommands: dict[str, tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all commands (eager + lazy), sorted."""
        return sorted({*super().list_commands(ctx), *self.lazy_subcommands})

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Get a command, importing it lazily on first use."""
        if cmd_name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[cmd_name][0]
            modname, attr = import_path.rsplit(".", 1)
            cmd: click.Command = getattr(importlib.import_module(modname), attr)
            return cmd
        return super().get_command(ctx, cmd_name)

    def format_commands(self, ctx: click.Context, formatter: Any) -> None:
        """List commands using static summaries so help imports nothing."""
        names = self.list_commands(ctx)
        if not names:
            return
        limit = formatter.width - 6 - max(len(name) for name in names)
        rows = []
        for name in names:
            if name in self.lazy_subcommands:
                summary = self.lazy_subcommands[name][1]
                if len(summary) > limit:
                    summary = summary[: max(limit - 3, 0)].rstrip() + "..."
            else:
                cmd = super().get_command(ctx, name)
                if cmd is None or cmd.hidden:
                    continue
                summary = cmd.get_short_help_str(limit)
            rows.append((name, summary))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)

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
