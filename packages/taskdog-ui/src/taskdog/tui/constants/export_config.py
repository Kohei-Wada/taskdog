"""Export format configuration for TUI export command."""

# Export format configuration
EXPORT_FORMAT_CONFIG: dict[str, dict[str, str]] = {
    "json": {"exporter_class": "JsonTaskExporter", "extension": "json"},
    "csv": {"exporter_class": "CsvTaskExporter", "extension": "csv"},
    "markdown": {"exporter_class": "MarkdownTableExporter", "extension": "md"},
}
"""Configuration for export formats including exporter class names and file extensions."""
