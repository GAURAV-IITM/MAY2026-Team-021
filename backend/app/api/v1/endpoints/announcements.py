from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
)
from app.models.enums import (
    AnnouncementAudience,
    AnnouncementCategory,
    AnnouncementPriority,
    AnnouncementStatus,
)
from app.schemas.announcement import (
    AnnouncementArchiveRequest,
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.common import PaginationMeta, SuccessResponse, error_responses
from app.services import announcement as announcement_service
from app.services.audit import AuditContext


router = APIRouter(
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(401, 403, 500),
)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get(
    "",
    response_model=AnnouncementListResponse,
    operation_id="listOwnerAnnouncements",
    summary="List owner announcements",
    description=(
        "Returns paginated announcements and filter-independent summary counts "
        "for the authenticated user's library."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-LIST"]},
)
def list_announcements(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    announcement_status: Annotated[
        AnnouncementStatus | None,
        Query(alias="status"),
    ] = None,
    category: AnnouncementCategory | None = None,
    priority: AnnouncementPriority | None = None,
    audience: AnnouncementAudience | None = None,
) -> AnnouncementListResponse:
    result = announcement_service.list_announcements(
        db,
        tenant.library_id,
        pagination,
        status=announcement_status,
        category=category,
        priority=priority,
        audience=audience,
    )
    return AnnouncementListResponse(
        message="Announcements fetched successfully.",
        data=result.announcements,
        meta=PaginationMeta(
            page=pagination.page,
            pageSize=pagination.page_size,
            totalItems=result.total,
            totalPages=(
                math.ceil(result.total / pagination.page_size)
                if result.total
                else 0
            ),
        ),
        summary=result.summary,
    )


@router.post(
    "",
    response_model=SuccessResponse[AnnouncementResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createOwnerAnnouncement",
    summary="Create an announcement",
    description=(
        "Creates a draft or scheduled announcement in the current library. "
        "Library and author fields are derived from authentication."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-CREATE"]},
)
def create_announcement(
    payload: AnnouncementCreate,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[AnnouncementResponse]:
    announcement = announcement_service.create_announcement(
        db,
        tenant.library_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Announcement created successfully.",
        data=announcement,
    )


@router.patch(
    "/{announcement_id}",
    response_model=SuccessResponse[AnnouncementResponse],
    operation_id="updateOwnerAnnouncement",
    summary="Update an announcement",
    description=(
        "Updates an eligible draft or scheduled announcement. Lifecycle "
        "commands must use the publish and archive endpoints."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-EDIT"]},
)
def update_announcement(
    announcement_id: uuid.UUID,
    payload: AnnouncementUpdate,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[AnnouncementResponse]:
    announcement = announcement_service.update_announcement(
        db,
        tenant.library_id,
        announcement_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Announcement updated successfully.",
        data=announcement,
    )


@router.post(
    "/{announcement_id}/publish",
    response_model=SuccessResponse[AnnouncementResponse],
    operation_id="publishOwnerAnnouncement",
    summary="Publish an announcement",
    description=(
        "Publishes a draft or scheduled announcement immediately and records "
        "the authenticated actor."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-PUBLISH"]},
)
def publish_announcement(
    announcement_id: uuid.UUID,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[AnnouncementResponse]:
    announcement = announcement_service.publish_announcement(
        db,
        tenant.library_id,
        announcement_id,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Announcement published successfully.",
        data=announcement,
    )


@router.post(
    "/{announcement_id}/archive",
    response_model=SuccessResponse[AnnouncementResponse],
    operation_id="archiveOwnerAnnouncement",
    summary="Archive an announcement",
    description=(
        "Archives an eligible announcement while preserving it for history."
    ),
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-ARCHIVE"]},
)
def archive_announcement(
    announcement_id: uuid.UUID,
    payload: AnnouncementArchiveRequest,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[AnnouncementResponse]:
    announcement = announcement_service.archive_announcement(
        db,
        tenant.library_id,
        announcement_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Announcement archived successfully.",
        data=announcement,
    )


@router.delete(
    "/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteOwnerAnnouncement",
    summary="Delete an eligible announcement",
    description=(
        "Soft-deletes a draft or archived announcement. Published and "
        "scheduled announcements must be archived first."
    ),
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["ANNOUNCEMENT-DELETE"]},
)
def delete_announcement(
    announcement_id: uuid.UUID,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> Response:
    announcement_service.delete_announcement(
        db,
        tenant.library_id,
        announcement_id,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
