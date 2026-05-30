"""Base classes for Presentation layer ViewModels.

ViewModels are immutable data structures holding the data a renderer needs,
free of domain entities. Some ViewModels add computed/formatted fields; others
(e.g. TaskRowViewModel) are plain data carriers and the renderer does the
formatting.

Design principles:
- ViewModels are frozen dataclasses (immutable)
- ViewModels do NOT contain domain entities (Task, etc.)
- Conversion from DTOs to ViewModels is done by presenters/ (e.g. TablePresenter)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseViewModel:
    """Base class for all ViewModels in the Presentation layer.

    All ViewModels should:
    1. Be immutable (frozen=True)
    2. Not reference domain entities
    """
