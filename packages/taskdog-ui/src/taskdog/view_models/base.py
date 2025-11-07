"""Base classes for Presentation layer ViewModels.

ViewModels are immutable data structures that contain only the data needed for
presentation/rendering. Unlike DTOs which may contain domain entities, ViewModels
should contain only primitive types and presentation-ready formatted strings.

Design principles:
- ViewModels are frozen dataclasses (immutable)
- ViewModels do NOT contain domain entities (Task, etc.)
- ViewModels contain presentation-ready data (formatted strings, computed values)
- Conversion from DTOs/Entities to ViewModels is done by Mappers
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseViewModel:
    """Base class for all ViewModels in the Presentation layer.

    All ViewModels should:
    1. Be immutable (frozen=True)
    2. Contain only presentation-ready data
    3. Not reference domain entities
    """

    pass
