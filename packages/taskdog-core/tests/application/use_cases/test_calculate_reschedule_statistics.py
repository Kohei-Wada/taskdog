"""Tests for CalculateRescheduleStatisticsUseCase."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from taskdog_core.application.dto.statistics_output import CalculateStatisticsInput
from taskdog_core.application.use_cases.calculate_reschedule_statistics import (
    CalculateRescheduleStatisticsUseCase,
)
from taskdog_core.domain.entities.audit_log import AuditLog


def _event(task_id: int, old: str | None, new: str | None) -> AuditLog:
    return AuditLog(
        timestamp=datetime(2026, 7, 14, 10, 0),
        operation="update_task",
        resource_type="task",
        success=True,
        resource_id=task_id,
        resource_name="task",
        old_values={"deadline": old},
        new_values={"deadline": new},
    )


class TestCalculateRescheduleStatisticsUseCase:
    def setup_method(self) -> None:
        self.audit_repository = MagicMock()
        self.use_case = CalculateRescheduleStatisticsUseCase(self.audit_repository)

    def test_all_period_queries_without_since(self) -> None:
        self.audit_repository.get_deadline_changes.return_value = []

        result = self.use_case.execute(CalculateStatisticsInput(period="all"))

        self.audit_repository.get_deadline_changes.assert_called_once_with(since=None)
        assert result.tasks_with_deadline == 0

    def test_7d_period_queries_with_since(self) -> None:
        self.audit_repository.get_deadline_changes.return_value = []

        self.use_case.execute(CalculateStatisticsInput(period="7d"))

        since = self.audit_repository.get_deadline_changes.call_args.kwargs["since"]
        expected = datetime.now() - timedelta(days=7)
        assert abs((since - expected).total_seconds()) < 5

    def test_30d_period_queries_with_since(self) -> None:
        self.audit_repository.get_deadline_changes.return_value = []

        self.use_case.execute(CalculateStatisticsInput(period="30d"))

        since = self.audit_repository.get_deadline_changes.call_args.kwargs["since"]
        expected = datetime.now() - timedelta(days=30)
        assert abs((since - expected).total_seconds()) < 5

    def test_analyzes_returned_events(self) -> None:
        self.audit_repository.get_deadline_changes.return_value = [
            _event(1, None, "2026-07-20T18:00:00"),
            _event(1, "2026-07-20T18:00:00", "2026-07-25T18:00:00"),
        ]

        result = self.use_case.execute(CalculateStatisticsInput(period="all"))

        assert result.tasks_with_deadline == 1
        assert result.total_reschedule_events == 1
