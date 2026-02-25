"""FastAPI application factory and configuration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from taskdog_core.shared.config_manager import ConfigManager
from taskdog_server import __version__
from taskdog_server.api.dependencies import initialize_api_context
from taskdog_server.api.middleware import LoggingMiddleware
from taskdog_server.api.routers import (
    analytics_router,
    audit_router,
    lifecycle_router,
    notes_router,
    relationships_router,
    tags_router,
    tasks_router,
    websocket_router,
)
from taskdog_server.config.server_config_manager import ServerConfigManager
from taskdog_server.infrastructure.logging.config import configure_logging
from taskdog_server.websocket.connection_manager import ConnectionManager


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Load configuration once for the entire app
    config = ConfigManager.load()
    server_config = ServerConfigManager.load()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """FastAPI lifespan context manager.

        Initializes logging, API context, and connection manager on startup.
        Stores all state in app.state for proper scoping.
        """
        # Startup: Configure logging first
        configure_logging()

        # Initialize API context and store in app.state
        api_context = initialize_api_context(config)
        app.state.api_context = api_context

        # Store server config in app.state (for authentication)
        app.state.server_config = server_config

        # Initialize ConnectionManager in app.state (for WebSocket)
        app.state.connection_manager = ConnectionManager()

        yield

        # Shutdown: Dispose shared database engine
        api_context.close()

    app = FastAPI(
        title="Taskdog API",
        description="Task management API with scheduling, dependencies, and analytics",
        version=__version__,
        lifespan=lifespan,
    )

    # Add logging middleware (should be first to log all requests)
    app.add_middleware(LoggingMiddleware)

    # Register routers
    app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(lifecycle_router, prefix="/api/v1/tasks", tags=["lifecycle"])
    app.include_router(
        relationships_router, prefix="/api/v1/tasks", tags=["relationships"]
    )
    app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])
    app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
    app.include_router(tags_router, prefix="/api/v1/tags", tags=["tags"])
    app.include_router(audit_router, prefix="/api/v1/audit-logs", tags=["audit"])
    app.include_router(websocket_router, tags=["websocket"])

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Taskdog API", "version": __version__}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


# Create app instance
app = create_app()
