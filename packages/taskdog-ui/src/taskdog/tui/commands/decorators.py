"""Decorators for TUI commands."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def require_selected_task[F: Callable[..., Any]](func: F) -> F:
    """Decorator to ensure a task is selected before executing the command.

    This decorator checks if a task is selected and shows a warning if not.
    It should be used on execute() methods of commands that require a selected task.

    Args:
        func: The function to decorate (should be an execute method)

    Returns:
        Decorated function with task selection check

    Example:
        @require_selected_task
        def execute(self) -> None:
            task_id = self.get_selected_task_id()  # Guaranteed to be non-None
            # ... command logic ...
    """

    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        task_id = self.get_selected_task_id()
        if task_id is None:
            self.notify_warning("No task selected")
            return None
        return func(self, *args, **kwargs)

    return cast(F, wrapper)
