"""Lazy-loading Click group.

Implements Click's LazyGroup pattern (see
https://click.palletsprojects.com/en/stable/complex/) so that no subcommand
module is imported until the command is actually invoked. ``--help`` lists
commands from the static summaries in ``lazy_subcommands`` instead of importing
them, keeping startup fast (importing a command drags in heavy deps such as
rich.markdown, markdown_it, pydantic DTOs, or Textual for ``tui``).

Reused by the root group (``TaskdogGroup``) and by every noun subgroup
(``dep``, ``tag``, ``db``, ``audit``).
"""

from __future__ import annotations

import importlib
from typing import Any

import click


class LazyGroup(click.Group):
    """A Click group whose subcommands are imported lazily on first use.

    ``lazy_subcommands`` maps ``name -> (import path "module.attr", summary)``.
    ``aliases`` maps an alias to a canonical command name; aliases resolve to the
    same command but are hidden from the command listing.
    """

    def __init__(
        self,
        *args: Any,
        lazy_subcommands: dict[str, tuple[str, str]] | None = None,
        aliases: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}
        self.aliases = aliases or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all commands (eager + lazy), sorted. Aliases are excluded."""
        return sorted({*super().list_commands(ctx), *self.lazy_subcommands})

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Get a command, resolving aliases and importing lazily on first use."""
        cmd_name = self.aliases.get(cmd_name, cmd_name)
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
