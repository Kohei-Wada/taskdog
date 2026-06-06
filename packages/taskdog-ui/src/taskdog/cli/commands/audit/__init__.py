"""Audit command group."""

from __future__ import annotations

from taskdog.cli.lazy_group import LazyGroup

audit_group = LazyGroup(
    name="audit",
    help="Inspect operation history (audit logs).",
    lazy_subcommands={
        "list": (
            "taskdog.cli.commands.audit.list.list_command",
            "Display operation history (audit logs).",
        ),
    },
)
