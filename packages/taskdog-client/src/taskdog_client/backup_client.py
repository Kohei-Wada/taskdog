"""Client for backup/restore endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx  # type: ignore[import-not-found]

from taskdog_core.application.dto.restore_result import RestoreResultDTO
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError

if TYPE_CHECKING:
    from pathlib import Path

    from taskdog_client.base_client import BaseApiClient

# Write the streamed snapshot in 1 MiB chunks.
_CHUNK_SIZE = 1024 * 1024


class BackupClient:
    """Download physical database snapshots and upload them for restore."""

    def __init__(self, base: BaseApiClient) -> None:
        """Initialize with a shared base client.

        Args:
            base: Shared BaseApiClient instance.
        """
        self._base = base

    def backup(self, output_path: Path) -> None:
        """Download a database snapshot and save it to output_path.

        Args:
            output_path: Local path to write the `.db` snapshot to.

        Raises:
            ServerConnectionError: If the connection to the server fails.
            TaskNotFoundException / TaskValidationError / AuthenticationError /
            ServerError: Mapped from non-success HTTP responses.
        """
        # Download to a temp file and atomically rename, so an interrupted
        # download never leaves a corrupt partial snapshot at output_path.
        tmp_path = output_path.with_name(output_path.name + ".part")
        try:
            with self._base.client.stream(
                "GET", "/api/v1/backup", headers=self._base.auth_headers()
            ) as response:
                if not response.is_success:
                    response.read()
                    self._base._handle_error(response)
                with tmp_path.open("wb") as out:
                    for chunk in response.iter_bytes(_CHUNK_SIZE):
                        out.write(chunk)
            tmp_path.replace(output_path)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            tmp_path.unlink(missing_ok=True)
            raise ServerConnectionError(self._base.base_url, e) from e
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise

    def restore(self, file_path: Path) -> RestoreResultDTO:
        """Upload a `.db` snapshot to stage a restore.

        Args:
            file_path: Local path to the `.db` snapshot to upload.

        Returns:
            RestoreResultDTO reporting the pending status.

        Raises:
            TaskValidationError: If the server rejects the upload (400).
            ServerConnectionError: If the connection to the server fails.
        """
        with file_path.open("rb") as upload:
            data = self._base._request_json(
                "post",
                "/api/v1/restore",
                files={"file": (file_path.name, upload, "application/octet-stream")},
            )
        return RestoreResultDTO.model_validate(data)
