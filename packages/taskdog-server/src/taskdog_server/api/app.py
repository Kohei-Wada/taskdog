"""FastAPI application factory and configuration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taskdog_core.shared.config_manager import ConfigManager
from taskdog_server.api.dependencies import initialize_api_context
from taskdog_server.api.middleware import LoggingMiddleware
from taskdog_server.api.routers import (
    analytics_router,
    lifecycle_router,
    notes_router,
    relationships_router,
    tasks_router,
    websocket_router,
)
from taskdog_server.infrastructure.logging.config import configure_logging
from taskdog_server.websocket.connection_manager import ConnectionManager


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Load configuration once for the entire app
    config = ConfigManager.load()

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

        # Initialize ConnectionManager in app.state (for WebSocket)
        app.state.connection_manager = ConnectionManager()

        yield

        # Shutdown: Cleanup (if needed in the future)
        pass

    app = FastAPI(
        title="Taskdog API",
        description="Task management API with scheduling, dependencies, and analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add logging middleware (should be first to log all requests)
    app.add_middleware(LoggingMiddleware)

    # Configure CORS with settings from config file or defaults
    # Default origins: localhost:3000, localhost:8000, 127.0.0.1:3000, 127.0.0.1:8000
    # Can be overridden in config.toml under [api] section with cors_origins = [...]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
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
    app.include_router(websocket_router, tags=["websocket"])

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
