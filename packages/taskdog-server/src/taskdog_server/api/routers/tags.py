"""Tag management endpoints."""

from fastapi import APIRouter

from taskdog_server.api.dependencies import (
    AuditLogControllerDep,
    AuthenticatedClientDep,
    RelationshipControllerDep,
)
from taskdog_server.api.error_handlers import handle_task_errors
from taskdog_server.api.models.responses import DeleteTagResponse

router = APIRouter()


@router.delete("/{tag_name}", response_model=DeleteTagResponse)
@handle_task_errors
async def delete_tag(
    tag_name: str,
    controller: RelationshipControllerDep,
    audit_controller: AuditLogControllerDep,
    client_name: AuthenticatedClientDep,
) -> DeleteTagResponse:
    """Delete a tag from the system.

    Removes the tag and all its associations with tasks.

    Args:
        tag_name: Name of the tag to delete
        controller: Relationship controller dependency
        audit_controller: Audit log controller dependency
        client_name: Authenticated client name

    Returns:
        Deleted tag name and number of affected tasks

    Raises:
        HTTPException: 404 if tag not found
    """
    result = controller.delete_tag(tag_name)

    # Audit log
    audit_controller.log_operation(
        operation="delete_tag",
        resource_type="tag",
        resource_id=None,
        resource_name=tag_name,
        client_name=client_name,
        old_values={"affected_task_count": result.affected_task_count},
        success=True,
    )

    return DeleteTagResponse(
        tag_name=result.tag_name,
        affected_task_count=result.affected_task_count,
    )
