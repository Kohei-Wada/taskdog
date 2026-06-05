"""Tests for the Gantt overlay produced by ListTasksUseCase (include_gantt)."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.application.queries.task_query_service import TaskQueryService
from taskdog_core.application.use_cases.list_tasks import ListTasksUseCase
from taskdog_core.domain.entities.task import TaskStatus
from tests.helpers.time_provider import FakeTimeProvider


class TestListTasksGanttOverlay:
    """Test the shared-fetch Gantt overlay path of ListTasksUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.query_service = TaskQueryService(self.repository, FakeTimeProvider())
        self.use_case = ListTasksUseCase(self.repository, self.query_service)

    def _execute(self, **kwargs):
        kwargs.setdefault("include_gantt", True)
        return self.use_case.execute(ListTasksInput(**kwargs))

    def test_returns_tasks_and_overlay(self):
        """Result carries the shared task list plus a Gantt overlay."""
        today = date.today()
        self.repository.create(
            name="Scheduled Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
            estimated_duration=16.0,
        )

        result = self._execute(include_archived=True)

        assert len(result.tasks) == 1
        assert result.gantt_data is not None
        assert result.gantt_data.date_range is not None

    def test_overlay_is_absent_when_not_requested(self):
        """Without include_gantt the overlay is not computed."""
        result = self._execute(include_gantt=False, include_archived=True)

        assert result.gantt_data is None

    def test_overlay_respects_chart_date_range(self):
        """Chart start/end dates drive the overlay date range."""
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=7)

        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
        )

        result = self._execute(
            include_archived=True,
            chart_start_date=start_date,
            chart_end_date=end_date,
        )

        assert result.gantt_data.date_range.start_date == start_date
        assert result.gantt_data.date_range.end_date == end_date

    def test_filters_by_status(self):
        """Status filter applies to the shared task list."""
        today = date.today()
        for name, status in [
            ("Pending", TaskStatus.PENDING),
            ("Completed", TaskStatus.COMPLETED),
        ]:
            self.repository.create(
                name=name,
                priority=1,
                status=status,
                planned_start=datetime.combine(today, datetime.min.time()),
                planned_end=datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ),
            )

        result = self._execute(include_archived=True, status="PENDING")

        assert [t.name for t in result.tasks] == ["Pending"]

    def test_filters_archived_by_default(self):
        """Archived tasks are excluded unless include_archived is set."""
        today = date.today()
        self.repository.create(
            name="Active",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )
        self.repository.create(
            name="Archived",
            priority=2,
            status=TaskStatus.PENDING,
            is_archived=True,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
        )

        result = self._execute(include_archived=False)

        assert [t.name for t in result.tasks] == ["Active"]

    def test_filters_by_tags(self):
        """Tag filter applies to the shared task list."""
        today = date.today()
        for name, tag in [("Work task", "work"), ("Personal task", "personal")]:
            self.repository.create(
                name=name,
                priority=1,
                status=TaskStatus.PENDING,
                tags=[tag],
                planned_start=datetime.combine(today, datetime.min.time()),
                planned_end=datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ),
            )

        result = self._execute(include_archived=True, tags=["work"])

        assert [t.name for t in result.tasks] == ["Work task"]

    def test_overlay_calculates_total_estimated_duration(self):
        """total_estimated_duration sums estimates of the fetched tasks."""
        today = date.today()
        for est in (8.0, 16.5, None):
            self.repository.create(
                name=f"Task {est}",
                priority=1,
                status=TaskStatus.PENDING,
                planned_start=datetime.combine(today, datetime.min.time()),
                planned_end=datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ),
                estimated_duration=est,
            )

        result = self._execute(include_archived=True)

        assert result.gantt_data.total_estimated_duration == 24.5

    def test_sorts_by_deadline(self):
        """Sorting applies to the shared task list."""
        today = date.today()
        for name, days in [("Later", 7), ("Sooner", 1)]:
            self.repository.create(
                name=name,
                priority=1,
                deadline=datetime.combine(
                    today + timedelta(days=days), datetime.min.time()
                ),
                planned_start=datetime.combine(today, datetime.min.time()),
                planned_end=datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ),
            )

        result = self._execute(include_archived=True, sort_by="deadline")

        assert [t.name for t in result.tasks] == ["Sooner", "Later"]

    def test_empty_for_no_tasks(self):
        """No tasks yields an empty list and a zero-total overlay."""
        result = self._execute(include_archived=True)

        assert result.tasks == []
        assert result.gantt_data.total_estimated_duration == 0.0

    def test_include_gantt_fetches_filtered_set_once(self):
        """Table + overlay share a single filtered fetch (no double query)."""
        today = date.today()
        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
        )

        with patch.object(
            self.query_service,
            "get_filtered_tasks",
            wraps=self.query_service.get_filtered_tasks,
        ) as spy:
            self._execute(include_archived=True)

        assert spy.call_count == 1
