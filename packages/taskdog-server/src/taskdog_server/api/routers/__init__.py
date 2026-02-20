"""API routers for FastAPI endpoints."""

from taskdog_server.api.routers.analytics import router as analytics_router
from taskdog_server.api.routers.audit import router as audit_router
from taskdog_server.api.routers.lifecycle import router as lifecycle_router
from taskdog_server.api.routers.notes import router as notes_router
from taskdog_server.api.routers.relationships import router as relationships_router
from taskdog_server.api.routers.tags import router as tags_router
from taskdog_server.api.routers.tasks import router as tasks_router
from taskdog_server.api.routers.websocket import router as websocket_router

__all__ = [
    "analytics_router",
    "audit_router",
    "lifecycle_router",
    "notes_router",
    "relationships_router",
    "tags_router",
    "tasks_router",
    "websocket_router",
]
