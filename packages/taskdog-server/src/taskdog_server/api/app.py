"""FastAPI application factory and configuration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taskdog_server.api.dependencies import initialize_api_context, set_api_context
from taskdog_server.api.routers import (
    analytics_router,
    lifecycle_router,
    notes_router,
    relationships_router,
    tasks_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager.

    Initializes API context on startup and cleans up on shutdown.
    """
    # Startup: Initialize API context
    api_context = initialize_api_context()
    set_api_context(api_context)

    yield

    # Shutdown: Cleanup (if needed in the future)
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Taskdog API",
        description="Task management API with scheduling, dependencies, and analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure from settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(lifecycle_router, prefix="/api/v1/tasks", tags=["lifecycle"])
    app.include_router(
        relationships_router, prefix="/api/v1/tasks", tags=["relationships"]
    )
    app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])
    app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Taskdog API", "version": "1.0.0"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


# Create app instance
app = create_app()
