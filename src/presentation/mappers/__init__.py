"""Presentation layer Mappers.

Mappers convert Application layer DTOs and Domain entities into
Presentation layer ViewModels for rendering in CLI/TUI.
"""

from presentation.mappers.base import Mapper
from presentation.mappers.statistics_mapper import StatisticsMapper

__all__ = ["Mapper", "StatisticsMapper"]
