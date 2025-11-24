"""UI-layer default values for convenience and display.

These are NOT business logic defaults (which are handled by the server).
They're used for:
- Placeholder text in forms
- Default values in date/time pickers
- UI convenience when values aren't provided by user

The actual business defaults are applied by server controllers based on
the Core config (config.toml). These UI defaults are intentionally hardcoded
to match the common business hour defaults for better user experience.

See also:
- Core config defaults: packages/taskdog-core/src/taskdog_core/shared/config_defaults.py
- Server applies actual defaults: packages/taskdog-server/src/taskdog_server/api/dependencies.py
"""

# Time defaults (match common business hours)
DEFAULT_START_HOUR = 9  # Business day start (9 AM)
DEFAULT_END_HOUR = 18  # Business day end (6 PM)

# Task defaults
DEFAULT_PRIORITY = 5  # Task priority placeholder (1-10 scale)
