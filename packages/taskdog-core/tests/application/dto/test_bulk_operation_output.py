"""Tests for BulkOperationOutput failure accounting."""

from taskdog_core.application.dto.bulk_operation_output import (
    BulkOperationOutput,
    BulkTaskResultOutput,
)


def _result(task_id: int, success: bool) -> BulkTaskResultOutput:
    return BulkTaskResultOutput(
        task_id=task_id,
        success=success,
        task=None,
        error=None if success else "boom",
    )


def test_no_failures_when_all_succeed():
    output = BulkOperationOutput(results=[_result(1, True), _result(2, True)])

    assert output.failure_count == 0
    assert output.has_failures is False


def test_counts_each_failed_result():
    output = BulkOperationOutput(
        results=[_result(1, True), _result(2, False), _result(3, False)]
    )

    assert output.failure_count == 2
    assert output.has_failures is True


def test_empty_batch_has_no_failures():
    output = BulkOperationOutput(results=[])

    assert output.failure_count == 0
    assert output.has_failures is False
