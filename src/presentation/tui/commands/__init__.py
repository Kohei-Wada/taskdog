"""TUI command classes for action handling.

This module imports all command classes to ensure their registration
with the command registry through the @command_registry.register decorator.
"""

# Import all commands to trigger registration
from presentation.tui.commands.add_task_command import AddTaskCommand
from presentation.tui.commands.cancel_task_command import CancelTaskCommand
from presentation.tui.commands.complete_task_command import CompleteTaskCommand
from presentation.tui.commands.delete_task_command import DeleteTaskCommand
from presentation.tui.commands.edit_note_command import EditNoteCommand
from presentation.tui.commands.edit_task_command import EditTaskCommand
from presentation.tui.commands.optimize_command import OptimizeCommand
from presentation.tui.commands.pause_task_command import PauseTaskCommand
from presentation.tui.commands.refresh_command import RefreshCommand
from presentation.tui.commands.reopen_task_command import ReopenTaskCommand
from presentation.tui.commands.show_details_command import ShowDetailsCommand
from presentation.tui.commands.start_task_command import StartTaskCommand

__all__ = [
    "AddTaskCommand",
    "CancelTaskCommand",
    "CompleteTaskCommand",
    "DeleteTaskCommand",
    "EditNoteCommand",
    "EditTaskCommand",
    "OptimizeCommand",
    "PauseTaskCommand",
    "RefreshCommand",
    "ReopenTaskCommand",
    "ShowDetailsCommand",
    "StartTaskCommand",
]
