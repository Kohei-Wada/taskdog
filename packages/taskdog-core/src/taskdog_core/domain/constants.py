"""Domain-level constants (business rules and physical constants).

This module contains constants that are part of the domain logic,
such as physical constants and business rules that are independent
of infrastructure, presentation, or shared utilities.
"""

# Physical constants - Time conversions
SECONDS_PER_HOUR = 3600
"""Number of seconds in one hour (physical constant)."""

# Validation limits - Business rules
MIN_PRIORITY_EXCLUSIVE = 0
"""Minimum priority value (exclusive). Priority must be > 0."""

MAX_TASK_NAME_LENGTH = 255
"""Maximum length of task name in characters."""

MAX_TAG_LENGTH = 50
"""Maximum length of a single tag in characters."""

MAX_TAGS_PER_TASK = 20
"""Maximum number of tags allowed per task."""
