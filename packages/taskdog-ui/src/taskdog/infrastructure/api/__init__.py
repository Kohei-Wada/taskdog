"""API client modules for Taskdog server communication.

This package contains specialized clients for different API domains,
following Clean Architecture principles and domain-driven design.
"""

from taskdog.infrastructure.api.analytics_client import AnalyticsClient
from taskdog.infrastructure.api.audit_client import AuditClient
from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog.infrastructure.api.lifecycle_client import LifecycleClient
from taskdog.infrastructure.api.notes_client import NotesClient
from taskdog.infrastructure.api.query_client import QueryClient
from taskdog.infrastructure.api.relationship_client import RelationshipClient
from taskdog.infrastructure.api.task_client import TaskClient

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
