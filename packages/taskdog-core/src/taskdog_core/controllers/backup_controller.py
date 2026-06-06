"""Controller for backup/restore operations."""

from collections.abc import Iterator

from taskdog_core.application.dto.restore_result import RestoreResultDTO
from taskdog_core.domain.services.backup_store import IBackupStore


class BackupController:
    """Unified backup/restore operations over a storage-neutral port."""

    def __init__(self, store: IBackupStore) -> None:
        """Initialize the controller.

        Args:
            store: Backup store implementation (e.g. SqliteBackupStore).
        """
        self._store = store

    def create_snapshot(self) -> Iterator[bytes]:
        """Stream a consistent snapshot of the store as byte chunks."""
        return self._store.create_snapshot()

    def restore(self, data: Iterator[bytes]) -> RestoreResultDTO:
        """Stage an uploaded snapshot to be applied on the next startup.

        Args:
            data: Iterator yielding the uploaded snapshot in chunks.

        Returns:
            RestoreResultDTO reporting the pending status.

        Raises:
            BackupValidationError: If the uploaded snapshot is invalid.
        """
        self._store.stage_restore(data)
        return RestoreResultDTO(status="pending", message="restart required")
