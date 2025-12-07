"""HTTP API client for Taskdog server.

This package provides a type-safe HTTP client for communicating with
the Taskdog API server. It handles authentication, error mapping,
and response conversion to domain DTOs.
"""

from taskdog_client.analytics_client import AnalyticsClient
from taskdog_client.audit_client import AuditClient
from taskdog_client.base_client import BaseApiClient
from taskdog_client.lifecycle_client import LifecycleClient
from taskdog_client.notes_client import NotesClient
from taskdog_client.query_client import QueryClient
from taskdog_client.relationship_client import RelationshipClient
from taskdog_client.task_client import TaskClient

__all__ = [
    "AnalyticsClient",
    "AuditClient",
    "BaseApiClient",
    "LifecycleClient",
    "NotesClient",
    "QueryClient",
    "RelationshipClient",
    "TaskClient",
]
