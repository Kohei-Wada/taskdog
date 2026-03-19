"""Tests for BulkTaskController."""

from unittest.mock import MagicMock, Mock

import pytest

from taskdog_core.application.dto.status_change_output import StatusChangeOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.controllers.bulk_task_controller import BulkTaskController
from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


def _make_task_output(task_id=1, name="Task", status=TaskStatus.IN_PROGRESS):
    task = Task(id=task_id, name=name, priority=1, status=status)
    return TaskOperationOutput.from_task(task)


def _make_status_change_output(
    task_id=1,
    name="Task",
    old_status=TaskStatus.PENDING,
    new_status=TaskStatus.IN_PROGRESS,
):
    task_output = _make_task_output(task_id=task_id, name=name, status=new_status)
    return StatusChangeOutput(task=task_output, old_status=old_status)


class TestBulkTaskController:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lifecycle = Mock(spec=TaskLifecycleController)
        self.crud = Mock(spec=TaskCrudController)
        self.query = Mock(spec=QueryController)
        self.controller = BulkTaskController(self.lifecycle, self.crud, self.query)

    # ── bulk_lifecycle ──────────────────────────────────────────────

    def test_bulk_lifecycle_all_success(self):
        self.lifecycle.start_task.side_effect = [
            _make_status_change_output(task_id=1),
            _make_status_change_output(task_id=2),
        ]

        output = self.controller.bulk_lifecycle([1, 2], "start")

        assert len(output.results) == 2
        assert all(r.success for r in output.results)
        assert all(r.task is not None for r in output.results)

    def test_bulk_lifecycle_all_failure(self):
        self.lifecycle.start_task.side_effect = TaskNotFoundException("not found")

        output = self.controller.bulk_lifecycle([1, 2], "start")

        assert len(output.results) == 2
        assert all(not r.success for r in output.results)
        assert all(r.error is not None for r in output.results)
        assert all(r.task is None for r in output.results)

    def test_bulk_lifecycle_mixed(self):
        self.lifecycle.start_task.side_effect = [
            _make_status_change_output(task_id=1),
            TaskNotFoundException("not found"),
        ]

        output = self.controller.bulk_lifecycle([1, 2], "start")

        assert len(output.results) == 2
        assert output.results[0].success is True
        assert output.results[1].success is False

    def test_bulk_lifecycle_invalid_operation_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid lifecycle operation"):
            self.controller.bulk_lifecycle([1], "invalid_op")

    def test_bulk_lifecycle_old_status_stored(self):
        self.lifecycle.complete_task.return_value = _make_status_change_output(
            task_id=1,
            old_status=TaskStatus.IN_PROGRESS,
            new_status=TaskStatus.COMPLETED,
        )

        output = self.controller.bulk_lifecycle([1], "complete")

        assert output.results[0].old_status == "IN_PROGRESS"

    @pytest.mark.parametrize(
        "operation", ["start", "complete", "pause", "cancel", "reopen"]
    )
    def test_bulk_lifecycle_all_operations_accepted(self, operation):
        method = getattr(self.lifecycle, f"{operation}_task")
        method.return_value = _make_status_change_output(task_id=1)

        output = self.controller.bulk_lifecycle([1], operation)

        assert len(output.results) == 1
        assert output.results[0].success is True

    # ── bulk_archive ────────────────────────────────────────────────

    def test_bulk_archive_all_success(self):
        self.crud.archive_task.side_effect = [
            _make_task_output(task_id=1),
            _make_task_output(task_id=2),
        ]

        output = self.controller.bulk_archive([1, 2])

        assert len(output.results) == 2
        assert all(r.success for r in output.results)

    def test_bulk_archive_mixed(self):
        self.crud.archive_task.side_effect = [
            _make_task_output(task_id=1),
            TaskNotFoundException("not found"),
        ]

        output = self.controller.bulk_archive([1, 2])

        assert output.results[0].success is True
        assert output.results[1].success is False

    # ── bulk_restore ────────────────────────────────────────────────

    def test_bulk_restore_all_success(self):
        self.crud.restore_task.side_effect = [
            _make_task_output(task_id=1),
            _make_task_output(task_id=2),
        ]

        output = self.controller.bulk_restore([1, 2])

        assert len(output.results) == 2
        assert all(r.success for r in output.results)

    def test_bulk_restore_failure(self):
        self.crud.restore_task.side_effect = TaskNotFoundException("not found")

        output = self.controller.bulk_restore([1])

        assert output.results[0].success is False

    # ── bulk_delete ─────────────────────────────────────────────────

    def test_bulk_delete_looks_up_task_name(self):
        task_detail = MagicMock()
        task_detail.task.name = "To Delete"
        self.query.get_task_by_id.return_value = task_detail

        output = self.controller.bulk_delete([1])

        assert output.results[0].success is True
        assert output.results[0].task is None
        assert output.results[0].task_name == "To Delete"
        self.query.get_task_by_id.assert_called_once_with(1)
        self.crud.remove_task.assert_called_once_with(1)

    def test_bulk_delete_nonexistent_task(self):
        task_detail = MagicMock()
        task_detail.task = None
        self.query.get_task_by_id.return_value = task_detail

        output = self.controller.bulk_delete([99])

        assert output.results[0].success is False
        assert "not found" in output.results[0].error.lower()

    def test_bulk_delete_mixed(self):
        task_detail = MagicMock()
        task_detail.task.name = "OK"
        self.query.get_task_by_id.side_effect = [
            task_detail,
            TaskNotFoundException("not found"),
        ]

        output = self.controller.bulk_delete([1, 2])

        assert output.results[0].success is True
        assert output.results[1].success is False
