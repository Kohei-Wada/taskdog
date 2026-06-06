"""Presentation-layer task status.

Mirrors the core domain ``TaskStatus`` values but is owned by the UI layer so
that presentation code does not depend on ``taskdog_core.domain`` directly.
Presenters map the string status carried by DTOs into this enum at the layer
boundary (``TaskStatus(dto.status.value)``).
"""

from enum import Enum


class TaskStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
