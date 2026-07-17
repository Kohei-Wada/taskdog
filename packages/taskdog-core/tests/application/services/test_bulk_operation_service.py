"""Tests for BulkOperationService."""

import pytest

from taskdog_core.application.services.bulk_operation_service import (
    BulkOperationService,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestBulkOperationService:
    @pytest.fixture(autouse=True)
    def setup(self, repository):
        self.repository = repository
        self.service = BulkOperationService(repository)

    def _add_task(self, name="Task", status=TaskStatus.PENDING, is_archived=False):
        task = Task(name=name, priority=1, status=status, is_archived=is_archived)
        self.repository.save(task)
        return task.id

    # ── bulk_lifecycle ──────────────────────────────────────────────

    def test_bulk_lifecycle_all_success(self):
        id1 = self._add_task(status=TaskStatus.PENDING)
        id2 = self._add_task(status=TaskStatus.PENDING)

        output = self.service.bulk_lifecycle([id1, id2], "start")

        assert len(output.results) == 2
        assert all(r.success for r in output.results)
        assert all(r.task is not None for r in output.results)
        assert all(r.old_status == "PENDING" for r in output.results)
        for tid in (id1, id2):
            assert self.repository.get_by_id(tid).status == TaskStatus.IN_PROGRESS

    def test_bulk_lifecycle_missing_tasks_fail(self):
        output = self.service.bulk_lifecycle([9998, 9999], "start")

        assert len(output.results) == 2
        assert all(not r.success for r in output.results)
        assert all(r.error is not None for r in output.results)
        assert all(r.task is None for r in output.results)

    def test_bulk_lifecycle_mixed(self):
        ok = self._add_task(status=TaskStatus.PENDING)

        output = self.service.bulk_lifecycle([ok, 9999], "start")

        assert output.results[0].success is True
        assert output.results[1].success is False
        assert output.has_failures is True
        assert output.failure_count == 1

    def test_bulk_lifecycle_invalid_operation_raises(self):
        with pytest.raises(ValueError, match="Invalid lifecycle operation"):
            self.service.bulk_lifecycle([1], "frobnicate")

    def test_bulk_lifecycle_preserves_order(self):
        id1 = self._add_task()
        id2 = self._add_task()

        output = self.service.bulk_lifecycle([id2, id1], "start")

        assert [r.task_id for r in output.results] == [id2, id1]

    # ── bulk_archive / bulk_restore ─────────────────────────────────

    def test_bulk_archive_success(self):
        id1 = self._add_task()

        output = self.service.bulk_archive([id1])

        assert output.results[0].success is True
        assert output.results[0].task is not None
        assert self.repository.get_by_id(id1).is_archived is True

    def test_bulk_restore_success(self):
        id1 = self._add_task(is_archived=True)

        output = self.service.bulk_restore([id1])

        assert output.results[0].success is True
        assert self.repository.get_by_id(id1).is_archived is False

    def test_bulk_archive_missing_task_fails(self):
        output = self.service.bulk_archive([9999])

        assert output.results[0].success is False
        assert output.results[0].error is not None

    # ── bulk_delete ─────────────────────────────────────────────────

    def test_bulk_delete_success_reports_name(self):
        id1 = self._add_task(name="Doomed")

        output = self.service.bulk_delete([id1])

        assert output.results[0].success is True
        assert output.results[0].task_name == "Doomed"
        assert self.repository.get_by_id(id1) is None

    def test_bulk_delete_missing_task_fails(self):
        output = self.service.bulk_delete([9999])

        assert output.results[0].success is False
        assert output.results[0].error is not None
