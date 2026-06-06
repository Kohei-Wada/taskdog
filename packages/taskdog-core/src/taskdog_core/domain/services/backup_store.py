"""Storage-neutral port for backup/restore of the data store."""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class IBackupStore(ABC):
    """Abstract interface for backing up and restoring the data store.

    The port is storage-neutral: it exposes only chunk streams, never database
    files, paths, or SQL. Storage specifics (SQLite, VACUUM INTO, file swaps)
    live solely in the infrastructure implementation.
    """

    @abstractmethod
    def create_snapshot(self) -> Iterator[bytes]:
        """Produce a consistent snapshot of the store as a stream of byte chunks.

        Returns:
            Iterator yielding the snapshot content in chunks.

        Raises:
            BackupNotSupportedError: If the store cannot be snapshotted.
        """

    @abstractmethod
    def stage_restore(self, data: Iterator[bytes]) -> None:
        """Validate an uploaded snapshot and place it into staging.

        The snapshot is applied on the next startup via apply_pending_restore;
        it is not applied live.

        Args:
            data: Iterator yielding the uploaded snapshot in chunks.

        Raises:
            BackupValidationError: If the uploaded snapshot is not valid.
            BackupNotSupportedError: If the store cannot be restored.
        """

    @abstractmethod
    def apply_pending_restore(self) -> bool:
        """Apply a previously staged snapshot, if any.

        Intended to run at startup before the store is opened.

        Returns:
            True if a staged snapshot was applied, False if there was none.
        """
