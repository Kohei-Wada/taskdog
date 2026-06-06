"""Custom exceptions for backup/restore operations."""


class BackupError(Exception):
    """Base exception for all backup/restore errors."""


class BackupValidationError(BackupError):
    """Raised when an uploaded backup fails validation (e.g. integrity check)."""


class BackupNotSupportedError(BackupError):
    """Raised when backup/restore is requested for a non-file store (e.g. in-memory)."""
