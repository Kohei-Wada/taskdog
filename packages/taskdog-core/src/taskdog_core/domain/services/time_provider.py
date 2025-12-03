"""Time provider interface for the domain layer.

This module defines the abstract interface for time-related functionality.
The actual implementation is provided by the infrastructure layer.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime


class ITimeProvider(ABC):
    """Abstract interface for providing current time.

    This interface allows time-dependent logic to be tested
    without patching the datetime module.
    """

    @abstractmethod
    def now(self) -> datetime:
        """Get the current datetime.

        Returns:
            Current datetime
        """
        ...

    @abstractmethod
    def today(self) -> date:
        """Get the current date.

        Returns:
            Current date
        """
        ...
