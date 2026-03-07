"""Timeline constants."""

# Display hour defaults (used by TimelinePresenter)
DEFAULT_START_HOUR = 8
DEFAULT_END_HOUR = 18
MIN_DISPLAY_HOURS = 2

# Timeline rendering constants (used by TimelineCellFormatter)
CHARS_PER_HOUR = 4
TIMELINE_BAR_CHAR = "\u2588"  # Full block character for work bars
TIMELINE_EMPTY_CHAR = " "

# Timeline table dimensions (used by RichTimelineRenderer)
TIMELINE_TABLE_DURATION_WIDTH = 6
