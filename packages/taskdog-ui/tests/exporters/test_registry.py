"""Tests for the shared export format registry."""

import pytest

from taskdog.exporters import (
    EXPORT_FILE_EXTENSIONS,
    EXPORTER_CLASSES,
    CsvTaskExporter,
    JsonTaskExporter,
    MarkdownTableExporter,
    create_exporter,
)


@pytest.mark.parametrize(
    ("export_format", "exporter_class"),
    [
        ("json", JsonTaskExporter),
        ("csv", CsvTaskExporter),
        ("markdown", MarkdownTableExporter),
    ],
)
def test_create_exporter_returns_format_exporter(
    export_format: str, exporter_class: type
) -> None:
    exporter = create_exporter(export_format, field_list=["id", "name"])

    assert type(exporter) is exporter_class
    assert exporter.field_list == ["id", "name"]


def test_create_exporter_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="Unsupported format: yaml"):
        create_exporter("yaml")


def test_every_format_has_a_file_extension() -> None:
    assert set(EXPORT_FILE_EXTENSIONS) == set(EXPORTER_CLASSES)
