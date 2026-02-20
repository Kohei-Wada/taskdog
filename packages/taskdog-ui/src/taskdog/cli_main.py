import importlib
from typing import Any

import click
from rich.console import Console

from taskdog import __version__
from taskdog.cli.commands.add import add_command
from taskdog.cli.commands.add_dependency import add_dependency_command
from taskdog.cli.commands.audit_logs import audit_logs_command
from taskdog.cli.commands.cancel import cancel_command
from taskdog.cli.commands.done import done_command
from taskdog.cli.commands.export import export_command
from taskdog.cli.commands.fix_actual import fix_actual_command
from taskdog.cli.commands.gantt import gantt_command
from taskdog.cli.commands.note import note_command
from taskdog.cli.commands.optimize import optimize_command
from taskdog.cli.commands.pause import pause_command
from taskdog.cli.commands.remove_dependency import remove_dependency_command
from taskdog.cli.commands.reopen import reopen_command
from taskdog.cli.commands.restore import restore_command
from taskdog.cli.commands.rm import rm_command
from taskdog.cli.commands.show import show_command
from taskdog.cli.commands.start import start_command
from taskdog.cli.commands.stats import stats_command
from taskdog.cli.commands.table import table_command
from taskdog.cli.commands.tags import tags_command
from taskdog.cli.commands.timeline import timeline_command
from taskdog.cli.commands.update import update_command
from taskdog.cli.context import CliContext
from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog.infrastructure.cli_config_manager import load_cli_config

# Lazy-loaded subcommands for performance optimization
# These commands have heavy dependencies (e.g., Textual) that slow down CLI startup
LAZY_SUBCOMMANDS: dict[str, str] = {
    "tui": "taskdog.cli.commands.tui.tui_command",
}


class TaskdogGroup(click.Group):
    """Custom Click Group with lazy loading and ASCII art help display.

    Implements Click's LazyGroup pattern to defer loading of heavy subcommands
    (like TUI with Textual) until they are actually invoked.
    See: https://click.palletsprojects.com/en/stable/complex/
    """

    def __init__(
        self,
        *args: Any,
        lazy_subcommands: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all commands including lazy-loaded ones."""
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Get a command, loading lazily if necessary."""
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name: str) -> click.Command:
        """Lazily load a command from its import path."""
        import_path = self.lazy_subcommands[cmd_name]
        modname, attr = import_path.rsplit(".", 1)
        mod = importlib.import_module(modname)
        cmd: click.Command = getattr(mod, attr)
        return cmd

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


cli.add_command(add_command)
cli.add_command(add_dependency_command)
cli.add_command(audit_logs_command)
cli.add_command(table_command)
cli.add_command(export_command)
cli.add_command(rm_command)
cli.add_command(update_command)
cli.add_command(start_command)
cli.add_command(pause_command)
cli.add_command(done_command)
cli.add_command(cancel_command)
cli.add_command(gantt_command)
cli.add_command(note_command)
cli.add_command(show_command)
cli.add_command(remove_dependency_command)
cli.add_command(reopen_command)
cli.add_command(restore_command)
cli.add_command(fix_actual_command)
cli.add_command(optimize_command)
cli.add_command(stats_command)
cli.add_command(tags_command)
cli.add_command(timeline_command)
# Note: tui_command is lazy-loaded via LAZY_SUBCOMMANDS for performance

if __name__ == "__main__":
    cli()
