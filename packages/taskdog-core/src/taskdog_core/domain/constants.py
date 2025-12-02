"""Domain-level constants (business rules and physical constants).

This module contains constants that are part of the domain logic,
such as physical constants and business rules that are independent
of infrastructure, presentation, or shared utilities.
"""

# Physical constants - Time conversions
SECONDS_PER_MINUTE = 60
"""Number of seconds in one minute (physical constant)."""

SECONDS_PER_HOUR = 3600
"""Number of seconds in one hour (physical constant)."""

SECONDS_PER_DAY = 86400
"""Number of seconds in one day (24 hours * 3600 seconds)."""

# File size validation
MIN_FILE_SIZE_FOR_CONTENT = 0
"""Minimum file size in bytes to consider a file as having content."""

# Validation limits - Business rules
MIN_PRIORITY_EXCLUSIVE = 0
"""Minimum priority value (exclusive). Priority must be > 0."""
