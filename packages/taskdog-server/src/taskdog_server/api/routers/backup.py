"""Backup/restore endpoints for the SQLite store."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from taskdog_core.application.dto.restore_result import RestoreResultDTO
from taskdog_server.api.dependencies import (
    AuthenticatedClientDep,
    BackupControllerDep,
)

router = APIRouter()


@router.get("/backup")
async def backup(
    controller: BackupControllerDep,
    _client_name: AuthenticatedClientDep,
) -> StreamingResponse:
    """Stream a consistent physical snapshot of the database as a `.db` file."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"taskdog-backup-{timestamp}.db"
    return StreamingResponse(
        controller.create_snapshot(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", response_model=RestoreResultDTO)
async def restore(
    controller: BackupControllerDep,
    _client_name: AuthenticatedClientDep,
    file: Annotated[UploadFile, File()],
) -> RestoreResultDTO:
    """Stage an uploaded `.db` snapshot to be applied on the next server restart."""
    data = await file.read()
    return controller.restore(iter([data]))
