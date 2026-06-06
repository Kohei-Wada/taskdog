"""Tag command group."""

from __future__ import annotations

from taskdog.cli.lazy_group import LazyGroup

tag_group = LazyGroup(
    name="tag",
    help="View, set, or delete task tags.",
    lazy_subcommands={
        "list": (
            "taskdog.cli.commands.tag.list.list_command",
            "List all tags, or the tags of a single task.",
        ),
        "set": (
            "taskdog.cli.commands.tag.set.set_command",
            "Set (replace) the tags of a task.",
        ),
        "rm": (
            "taskdog.cli.commands.tag.remove.remove_command",
            "Delete a tag from the system (removes it from all tasks).",
        ),
    },
)
