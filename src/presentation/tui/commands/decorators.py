"""Decorators for TUI commands."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def handle_tui_errors(action_name: str) -> Callable[[F], F]:
    """Decorator to handle errors in TUI commands.

    Catches exceptions during command execution and displays
    error notifications using the command's notify_error method.

    Args:
        action_name: Description of the action being performed (e.g., "starting task")

    Returns:
        Decorated function with error handling

    Example:
        @handle_tui_errors("starting task")
        def execute(self) -> None:
            task = self.get_selected_task()
            # ... command logic ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Use the command's notify_error method
                self.notify_error(f"Error {action_name}", e)
                return None

        return wrapper  # type: ignore

    return decorator
