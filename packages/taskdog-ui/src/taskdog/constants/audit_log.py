"""Audit log constants (CLI/TUI shared)."""

from taskdog.constants.common import JustifyValue

# Audit Log Table headers
HEADER_AUDIT_TIMESTAMP = "Timestamp"
HEADER_AUDIT_CLIENT = "Client"
HEADER_AUDIT_OPERATION = "Operation"
HEADER_AUDIT_RESOURCE = "Resource"
HEADER_AUDIT_STATUS = "Status"
HEADER_AUDIT_CHANGES = "Changes"
HEADER_AUDIT_STATUS_SHORT = "St"

# Audit Log Table Dimensions (CLI)
AUDIT_ID_WIDTH = 6
AUDIT_TIMESTAMP_WIDTH = 19
AUDIT_CLIENT_WIDTH = 15
AUDIT_OPERATION_WIDTH = 18
AUDIT_CHANGES_WIDTH = 30
AUDIT_STATUS_WIDTH = 8

# Audit Log Table Dimensions (TUI)
AUDIT_TUI_ID_WIDTH = 5
AUDIT_TUI_NAME_WIDTH = 25
AUDIT_TUI_CHANGES_WIDTH = 40
AUDIT_TUI_STATUS_WIDTH = 4

# Audit log column styles
COLUMN_AUDIT_ID_STYLE = "dim"
COLUMN_AUDIT_STATUS_OK_STYLE = "green"
COLUMN_AUDIT_STATUS_FAIL_STYLE = "red"

# Audit log column justify
JUSTIFY_AUDIT_TIMESTAMP: JustifyValue = "center"
JUSTIFY_AUDIT_ID: JustifyValue = "center"
JUSTIFY_AUDIT_NAME: JustifyValue = "left"
JUSTIFY_AUDIT_OPERATION: JustifyValue = "center"
JUSTIFY_AUDIT_CHANGES: JustifyValue = "left"
JUSTIFY_AUDIT_CLIENT: JustifyValue = "center"
JUSTIFY_AUDIT_STATUS: JustifyValue = "center"
JUSTIFY_AUDIT_RESOURCE: JustifyValue = "left"
