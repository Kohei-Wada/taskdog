"""Regression tests: every exporter renders the same default columns."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime

import pytest

from taskdog.exporters import (
    CsvTaskExporter,
    JsonTaskExporter,
    MarkdownTableExporter,
)
from taskdog.exporters.task_exporter import DEFAULT_EXPORT_FIELDS
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


@pytest.fixture
def task() -> TaskRowDto:
    return TaskRowDto(
        id=1,
        name="Default Fields Probe",
        priority=2,
        status=TaskStatus.PENDING,
        is_fixed=False,
        depends_on=[],
        tags=["never-shown-by-default"],
        estimated_duration=4.0,
        actual_duration_hours=None,
        planned_start=datetime(2025, 1, 1, 9, 0),
        planned_end=datetime(2025, 1, 1, 13, 0),
        actual_start=None,
        actual_end=None,
        deadline=datetime(2025, 1, 5, 18, 0),
        created_at=datetime(2024, 12, 31, 10, 0),
        updated_at=datetime(2024, 12, 31, 10, 0),
        is_archived=False,
        is_finished=False,
    )


def _markdown_header_fields(table: str) -> list[str]:
    header = table.splitlines()[0]
    return list(header.strip("|").split("|"))


def test_json_default_keys_match_shared_fields(task: TaskRowDto) -> None:
    result = json.loads(JsonTaskExporter().export([task]))
    assert list(result[0].keys()) == DEFAULT_EXPORT_FIELDS


def test_csv_default_columns_match_shared_fields(task: TaskRowDto) -> None:
    reader = csv.DictReader(io.StringIO(CsvTaskExporter().export([task])))
    assert list(reader.fieldnames or []) == DEFAULT_EXPORT_FIELDS


def test_markdown_default_columns_match_shared_fields(task: TaskRowDto) -> None:
    table = MarkdownTableExporter().export([task])
    expected = [field.replace("_", " ").title() for field in DEFAULT_EXPORT_FIELDS]
    assert _markdown_header_fields(table) == expected


def test_default_fields_exclude_internal_flags(task: TaskRowDto) -> None:
    # Tags/depends_on/is_* are intentionally opt-in; verify none leak by default.
    json_result = JsonTaskExporter().export([task])
    csv_result = CsvTaskExporter().export([task])
    md_result = MarkdownTableExporter().export([task])
    for hidden in ("tags", "depends_on", "is_fixed", "is_archived", "is_finished"):
        assert hidden not in json_result
        assert hidden not in csv_result
        assert hidden.replace("_", " ").title() not in md_result
