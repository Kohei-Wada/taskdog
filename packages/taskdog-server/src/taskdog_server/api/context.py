"""API context for dependency injection."""

from dataclasses import dataclass

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.holiday_checker import IHolidayChecker
from taskdog_core.domain.services.time_provider import ITimeProvider
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (
    SqliteAuditLogRepository,
)
from taskdog_core.shared.config_manager import Config


@dataclass
class ApiContext:
    """Context object for API endpoints containing shared dependencies.

    Attributes:
        repository: Task repository for data access
        config: Application configuration
        notes_repository: Notes repository for notes file operations
        query_controller: Controller for task read operations
        lifecycle_controller: Controller for task lifecycle operations (start, complete, etc.)
        relationship_controller: Controller for task relationships (dependencies, tags, hours)
        analytics_controller: Controller for analytics operations (statistics, optimization)
        crud_controller: Controller for CRUD operations (create, update, archive, etc.)
        holiday_checker: Holiday checker for workday validation (optional)
        time_provider: Time provider for current time (optional, defaults to SystemTimeProvider)
        audit_log_repository: Audit log repository for tracking API operations
    """

    repository: TaskRepository
    config: Config
    notes_repository: NotesRepository
    query_controller: QueryController
    lifecycle_controller: TaskLifecycleController
    relationship_controller: TaskRelationshipController
    analytics_controller: TaskAnalyticsController
    crud_controller: TaskCrudController
    holiday_checker: IHolidayChecker | None
    time_provider: ITimeProvider
    audit_log_repository: SqliteAuditLogRepository
