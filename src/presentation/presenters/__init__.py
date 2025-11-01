"""Presenters for converting DTOs to ViewModels.

Presenters are responsible for transforming application layer DTOs into
presentation layer ViewModels. They encapsulate the mapping logic and
ensure the presentation layer remains independent from domain entities.
"""

from presentation.presenters.gantt_presenter import GanttPresenter
from presentation.presenters.table_presenter import TablePresenter

__all__ = ["GanttPresenter", "TablePresenter"]
