"""Command registry for TUI commands.

This module provides a centralized registry for managing TUI commands,
allowing for automatic command registration and dynamic command execution.
"""

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from taskdog.tui.commands.base import TUICommandBase

# Type variable for command classes
TCommand = TypeVar("TCommand", bound="TUICommandBase")


class CommandRegistry:
    """Registry for managing TUI command classes.

    This class maintains a mapping between command names and their
    corresponding command classes, enabling dynamic command execution
    and reducing boilerplate in the main application.

    Supports both eager registration (via decorator) and lazy registration
    (deferred import) for improved startup performance.
    """

    def __init__(self) -> None:
        """Initialize an empty command registry."""
        self._commands: dict[str, type[TUICommandBase]] = {}
        self._lazy_commands: dict[str, str] = {}  # name -> module_path mapping

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

    def register_lazy(self, name: str, module_path: str) -> None:
        """Register a command for lazy loading.

        The command module will not be imported until the command is first accessed
        via get(). This improves startup performance by deferring imports.

        Args:
            name: The command name (used as action identifier)
            module_path: Module path in format "module.path:ClassName"
                        e.g., "taskdog.tui.commands.start_task_command:StartTaskCommand"
        """
        self._lazy_commands[name] = module_path

    def get(self, name: str) -> type["TUICommandBase"] | None:
        """Get a command class by name.

        If the command is registered for lazy loading and not yet imported,
        it will be imported on first access.

        Args:
            name: The command name

        Returns:
            The command class, or None if not found
        """
        # Return already loaded command
        if name in self._commands:
            return self._commands[name]

        # Lazy load if registered
        if name in self._lazy_commands:
            self._load_command(name)
            return self._commands.get(name)

        return None

    def _load_command(self, name: str) -> None:
        """Load a lazily registered command.

        Args:
            name: The command name to load
        """
        module_path = self._lazy_commands[name]
        try:
            # Parse "module.path:ClassName" format
            module_name, class_name = module_path.split(":")
            # Import the module (this triggers @register decorator)
            module = importlib.import_module(module_name)
            # Get the class from module
            command_class = getattr(module, class_name)
            # Store in commands dict (may already be there from decorator)
            self._commands[name] = command_class
            # Remove from lazy registry
            del self._lazy_commands[name]
        except (ImportError, AttributeError, ValueError) as e:
            # Log error but don't crash - command will remain unavailable
            print(f"Warning: Failed to load command '{name}' from '{module_path}': {e}")

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
