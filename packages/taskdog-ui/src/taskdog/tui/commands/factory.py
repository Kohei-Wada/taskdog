"""Command factory for TUI commands.

This module provides a factory for creating command instances with
proper dependency injection, reducing boilerplate and centralizing
command creation logic.
"""

from typing import TYPE_CHECKING, Any

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.context import TUIContext

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class CommandFactory:
    """Factory for creating TUI command instances.

    This class provides a centralized way to create command instances
    with proper dependency injection, reducing repetitive code in the
    main application.
    """

    def __init__(
        self,
        app: "TaskdogTUI",
        context: TUIContext,
    ):
        """Initialize the command factory.

        Args:
            app: The TaskdogTUI application instance
            context: TUI context with dependencies
        """
        self.app = app
        self.context = context

    def create(
        self,
        command_name: str,
        **kwargs: Any,
    ) -> TUICommandBase | None:
        """Create a command instance by name.

        Args:
            command_name: The name of the command to create
            **kwargs: Additional keyword arguments to pass to the command constructor

        Returns:
            Command instance, or None if command not found
        """
        command_class = command_registry.get(command_name)
        if command_class is None:
            return None

        # Create command with standard dependencies plus any additional kwargs
        return command_class(
            app=self.app,
            context=self.context,
            **kwargs,
        )

    def execute(self, command_name: str, **kwargs: Any) -> None:
        """Create and execute a command by name.

        Args:
            command_name: The name of the command to execute
            **kwargs: Additional keyword arguments to pass to the command constructor
        """
        command = self.create(command_name, **kwargs)
        if command:
            command.execute()
