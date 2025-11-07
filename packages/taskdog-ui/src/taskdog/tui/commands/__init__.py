"""TUI command classes for action handling.

This module uses lazy registration to defer command imports until they are
actually needed, significantly improving TUI startup performance.
"""

from taskdog.tui.commands.registry import command_registry

# Lazy command registration - modules are imported only when commands are first used
# Format: "command_name": "module.path:ClassName"
_LAZY_COMMANDS = {
    "add_task": "presentation.tui.commands.add_task_command:AddTaskCommand",
    "cancel_task": "presentation.tui.commands.cancel_task_command:CancelTaskCommand",
    "done_task": "presentation.tui.commands.complete_task_command:CompleteTaskCommand",
    "delete_task": "presentation.tui.commands.delete_task_command:DeleteTaskCommand",
    "hard_delete_task": "presentation.tui.commands.hard_delete_task_command:HardDeleteTaskCommand",
    "edit_note": "presentation.tui.commands.edit_note_command:EditNoteCommand",
    "edit_task": "presentation.tui.commands.edit_task_command:EditTaskCommand",
    "optimize": "presentation.tui.commands.optimize_command:OptimizeCommand",
    "pause_task": "presentation.tui.commands.pause_task_command:PauseTaskCommand",
    "refresh": "presentation.tui.commands.refresh_command:RefreshCommand",
    "reopen_task": "presentation.tui.commands.reopen_task_command:ReopenTaskCommand",
    "show_details": "presentation.tui.commands.show_details_command:ShowDetailsCommand",
    "start_task": "presentation.tui.commands.start_task_command:StartTaskCommand",
}

# Register all commands for lazy loading
for command_name, module_path in _LAZY_COMMANDS.items():
    command_registry.register_lazy(command_name, module_path)

__all__ = [
    "command_registry",
]
