"""TUI command classes for action handling.

This module uses lazy registration to defer command imports until they are
actually needed, significantly improving TUI startup performance.
"""

from taskdog.tui.commands.registry import command_registry

# Lazy command registration - modules are imported only when commands are first used
# Format: "command_name": "module.path:ClassName"
_LAZY_COMMANDS = {
    "add": "taskdog.tui.commands.add:AddCommand",
    "cancel": "taskdog.tui.commands.cancel:CancelCommand",
    "done": "taskdog.tui.commands.done:DoneCommand",
    "edit": "taskdog.tui.commands.edit:EditCommand",
    "export": "taskdog.tui.commands.export_command:ExportCommand",
    "hard_delete": "taskdog.tui.commands.hard_delete:HardDeleteCommand",
    "note": "taskdog.tui.commands.note:NoteCommand",
    "optimize": "taskdog.tui.commands.optimize_command:OptimizeCommand",
    "pause": "taskdog.tui.commands.pause:PauseCommand",
    "refresh": "taskdog.tui.commands.refresh_command:RefreshCommand",
    "reopen": "taskdog.tui.commands.reopen:ReopenCommand",
    "rm": "taskdog.tui.commands.rm:RmCommand",
    "show": "taskdog.tui.commands.show:ShowCommand",
    "show_help": "taskdog.tui.commands.help_command:ShowHelpCommand",
    "start": "taskdog.tui.commands.start:StartCommand",
}

# Register all commands for lazy loading
for command_name, module_path in _LAZY_COMMANDS.items():
    command_registry.register_lazy(command_name, module_path)

__all__ = [
    "command_registry",
]
