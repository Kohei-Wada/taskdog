"""FastAPI exception handlers.

Registers application-wide handlers that translate domain exceptions into
appropriate HTTP responses, so individual endpoints don't need to repeat
try/except blocks.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


async def _not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Map not-found domain exceptions to 404 NOT_FOUND."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


async def _bad_request_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Map validation domain exceptions to 400 BAD_REQUEST."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI app.

    - TaskNotFoundException, TagNotFoundException -> 404 NOT_FOUND
    - TaskValidationError (and subclasses) -> 400 BAD_REQUEST

    Starlette resolves handlers by walking the exception's MRO, so registering
    TaskValidationError also covers TaskAlreadyFinishedError, TaskNotStartedError,
    and the other validation subclasses.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(TaskNotFoundException, _not_found_handler)
    app.add_exception_handler(TagNotFoundException, _not_found_handler)
    app.add_exception_handler(TaskValidationError, _bad_request_handler)
