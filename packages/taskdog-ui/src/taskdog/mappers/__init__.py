"""Presentation layer Mappers.

Mappers convert Application layer DTOs and Domain entities into
Presentation layer ViewModels for rendering in CLI/TUI.
"""

from taskdog.mappers.statistics_mapper import StatisticsMapper

__all__ = ["StatisticsMapper"]
