"""TUI command classes for action handling."""

from taskdog.tui.commands.add import AddCommand
from taskdog.tui.commands.audit import AuditCommand
from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.cancel import CancelCommand
from taskdog.tui.commands.done import DoneCommand
from taskdog.tui.commands.edit import EditCommand
from taskdog.tui.commands.export_command import ExportCommand
from taskdog.tui.commands.fix_actual import FixActualCommand
from taskdog.tui.commands.hard_delete import HardDeleteCommand
from taskdog.tui.commands.help_command import ShowHelpCommand
from taskdog.tui.commands.note import NoteCommand
from taskdog.tui.commands.optimize_command import OptimizeCommand
from taskdog.tui.commands.pause import PauseCommand
from taskdog.tui.commands.refresh_command import RefreshCommand
from taskdog.tui.commands.reopen import ReopenCommand
from taskdog.tui.commands.rm import RmCommand
from taskdog.tui.commands.show import ShowCommand
from taskdog.tui.commands.start import StartCommand

COMMANDS: dict[str, type[TUICommandBase]] = {
    "add": AddCommand,
    "audit": AuditCommand,
    "cancel": CancelCommand,
    "done": DoneCommand,
    "edit": EditCommand,
    "export": ExportCommand,
    "fix_actual": FixActualCommand,
    "hard_delete": HardDeleteCommand,
    "show_help": ShowHelpCommand,
    "note": NoteCommand,
    "optimize": OptimizeCommand,
    "pause": PauseCommand,
    "refresh": RefreshCommand,
    "reopen": ReopenCommand,
    "rm": RmCommand,
    "show": ShowCommand,
    "start": StartCommand,
}

__all__ = ["COMMANDS"]
