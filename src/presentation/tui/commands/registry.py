"""Command registry for TUI commands.

This module provides a centralized registry for managing TUI commands,
allowing for automatic command registration and dynamic command execution.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from presentation.tui.commands.base import TUICommandBase

# Type variable for command classes
TCommand = TypeVar("TCommand", bound="TUICommandBase")


class CommandRegistry:
    """Registry for managing TUI command classes.

    This class maintains a mapping between command names and their
    corresponding command classes, enabling dynamic command execution
    and reducing boilerplate in the main application.
    """

    def __init__(self):
        """Initialize an empty command registry."""
        self._commands: dict[str, type[TUICommandBase]] = {}

    def register(self, name: str) -> Callable[[type[TCommand]], type[TCommand]]:
        """Decorator to register a command class.

        Args:
            name: The command name (used as action identifier)

        Returns:
            Decorator function that registers the command class

        Example:
            @command_registry.register("add_task")
            class AddTaskCommand(TUICommandBase):
                ...
        """

        def decorator(command_class: type[TCommand]) -> type[TCommand]:
            """Register the command class.

            Args:
                command_class: The command class to register

            Returns:
                The same command class (allows chaining)
            """
            self._commands[name] = command_class
            return command_class

        return decorator

    def get(self, name: str) -> type["TUICommandBase"] | None:
        """Get a command class by name.

        Args:
            name: The command name

        Returns:
            The command class, or None if not found
        """
        return self._commands.get(name)

    def has(self, name: str) -> bool:
        """Check if a command is registered.

        Args:
            name: The command name

        Returns:
            True if the command is registered, False otherwise
        """
        return name in self._commands

    def list_commands(self) -> list[str]:
        """Get a list of all registered command names.

        Returns:
            List of command names
        """
        return list(self._commands.keys())


# Global registry instance
command_registry = CommandRegistry()
