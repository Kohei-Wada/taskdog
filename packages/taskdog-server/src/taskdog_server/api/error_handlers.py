"""FastAPI error handling decorators.

Provides reusable decorators for common error handling patterns in API endpoints.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException, status

from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
    TaskNotStartedError,
    TaskValidationError,
)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


def handle_task_errors(func: F) -> F:
    """Decorator for common task operation error handling.

    Catches domain exceptions and converts them to appropriate HTTP exceptions:
    - TaskNotFoundException → 404 NOT_FOUND
    - TaskValidationError, TaskAlreadyFinishedError, TaskNotStartedError → 400 BAD_REQUEST

    Usage:
        @router.post("/{task_id}/start")
        @handle_task_errors
        async def start_task(task_id: int, ...):
            result = controller.start_task(task_id)
            return convert_to_response(result)

    Args:
        func: Async function to wrap with error handling

    Returns:
        Wrapped function with automatic error handling
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except (TaskNotFoundException, TagNotFoundException) as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        except (
            TaskValidationError,
            TaskAlreadyFinishedError,
            TaskNotStartedError,
        ) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e

    return wrapper  # type: ignore[return-value]
