"""Dependency command group."""

from __future__ import annotations

from taskdog.cli.lazy_group import LazyGroup

dep_group = LazyGroup(
    name="dep",
    help="Manage task dependencies.",
    lazy_subcommands={
        "add": (
            "taskdog.cli.commands.dep.add.add_command",
            "Add a dependency to a task.",
        ),
        "rm": (
            "taskdog.cli.commands.dep.remove.remove_command",
            "Remove a dependency from a task.",
        ),
    },
)
