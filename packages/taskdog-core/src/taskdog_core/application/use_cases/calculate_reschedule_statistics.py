"""Use case for calculating deadline reschedule statistics."""

from datetime import datetime, timedelta

from taskdog_core.application.dto.statistics_output import (
    CalculateStatisticsInput,
    RescheduleStatistics,
)
from taskdog_core.application.services.reschedule_analyzer import RescheduleAnalyzer
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.audit_log_repository import AuditLogRepository

_PERIOD_DAYS = {"7d": 7, "30d": 30}


class CalculateRescheduleStatisticsUseCase(
    UseCase[CalculateStatisticsInput, RescheduleStatistics]
):
    """Use case for calculating deadline reschedule statistics.

    Reads deadline-change events from the audit log and derives
    rescheduling behavior statistics. Period filtering applies to the
    audit log timestamps, not the task deadlines.
    """

    def __init__(self, audit_log_repository: AuditLogRepository):
        """Initialize the use case.

        Args:
            audit_log_repository: Repository for reading audit logs
        """
        self.audit_log_repository = audit_log_repository
        self.analyzer = RescheduleAnalyzer()

    def execute(self, input_dto: CalculateStatisticsInput) -> RescheduleStatistics:
        """Execute the reschedule statistics calculation.

        Args:
            input_dto: Input containing the period ('7d', '30d', or 'all')

        Returns:
            RescheduleStatistics for the period
        """
        days = _PERIOD_DAYS.get(input_dto.period)
        since = datetime.now() - timedelta(days=days) if days else None
        events = self.audit_log_repository.get_deadline_changes(since=since)
        return self.analyzer.calculate(events)
