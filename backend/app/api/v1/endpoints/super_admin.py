from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.api.deps import CurrentUser, DatabaseSession, Pagination, require_super_admin
from app.models.enums import LibraryStatus
from app.schemas.common import PaginationMeta, error_responses
from app.schemas.platform import (
    PlatformLibraryCreate,
    PlatformLibraryListResponse,
    PlatformLibraryOwnerAssign,
    PlatformLibraryStatusUpdate,
    PlatformLibrarySuccessResponse,
    PlatformLibraryUpdate,
    PlatformOwnerOptionListResponse,
)
from app.services import platform as platform_service
from app.services.audit import AuditContext


router = APIRouter(
    dependencies=[Depends(require_super_admin)],
    responses=error_responses(401, 403, 500),
)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


LibraryId = Annotated[uuid.UUID, Path(alias="libraryId")]


@router.get(
    "/libraries",
    response_model=PlatformLibraryListResponse,
    operation_id="listPlatformLibraries",
    summary="List platform libraries",
    description=(
        "Returns a searchable, filterable, sortable, paginated platform-wide "
        "library list for Super Admin users only."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-LIST"]},
)
def list_libraries(
    db: DatabaseSession,
    pagination: Pagination,
    library_status: Annotated[
        LibraryStatus | None,
        Query(alias="status"),
    ] = None,
    owner_id: Annotated[
        uuid.UUID | None,
        Query(alias="ownerId"),
    ] = None,
    state: Annotated[str | None, Query(max_length=100)] = None,
) -> PlatformLibraryListResponse:
    result = platform_service.list_libraries(
        db,
        pagination,
        status=library_status,
        owner_id=owner_id,
        state=state,
    )
    return PlatformLibraryListResponse(
        message="Libraries fetched successfully.",
        data=result.libraries,
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
    "/libraries",
    response_model=PlatformLibrarySuccessResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createPlatformLibrary",
    summary="Create a platform library",
    description=(
        "Creates a pending library and default settings, with optional "
        "assignment of an eligible existing owner."
    ),
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-CREATE"]},
)
def create_library(
    payload: PlatformLibraryCreate,
    request: Request,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PlatformLibrarySuccessResponse:
    library = platform_service.create_library(
        db,
        payload,
        current_user.id,
        audit_context=_audit_context(request),
    )
    return PlatformLibrarySuccessResponse(
        message="Library created successfully.",
        data=library,
    )


@router.get(
    "/libraries/owner-options",
    response_model=PlatformOwnerOptionListResponse,
    operation_id="listPlatformLibraryOwnerOptions",
    summary="List eligible library owners",
    description=(
        "Returns active, non-deleted users eligible for explicit primary-owner "
        "assignment."
    ),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-OWNER-ASSIGN"]},
)
def list_owner_options(db: DatabaseSession) -> PlatformOwnerOptionListResponse:
    return PlatformOwnerOptionListResponse(
        message="Owner options fetched successfully.",
        data=platform_service.list_eligible_owners(db),
    )


@router.get(
    "/libraries/{libraryId}",
    response_model=PlatformLibrarySuccessResponse,
    operation_id="getPlatformLibrary",
    summary="Get platform library details",
    description=(
        "Returns non-sensitive library profile, owner, counts, lifecycle "
        "metadata, and timestamps."
    ),
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-DETAIL"]},
)
def get_library(
    library_id: LibraryId,
    db: DatabaseSession,
) -> PlatformLibrarySuccessResponse:
    return PlatformLibrarySuccessResponse(
        message="Library fetched successfully.",
        data=platform_service.get_library(db, library_id),
    )


@router.patch(
    "/libraries/{libraryId}",
    response_model=PlatformLibrarySuccessResponse,
    operation_id="updatePlatformLibrary",
    summary="Edit a platform library",
    description=(
        "Updates approved profile fields while keeping code, status, owner, "
        "and lifecycle fields immutable."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-EDIT"]},
)
def update_library(
    library_id: LibraryId,
    payload: PlatformLibraryUpdate,
    request: Request,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PlatformLibrarySuccessResponse:
    library = platform_service.update_library(
        db,
        library_id,
        payload,
        current_user.id,
        audit_context=_audit_context(request),
    )
    return PlatformLibrarySuccessResponse(
        message="Library updated successfully.",
        data=library,
    )


@router.patch(
    "/libraries/{libraryId}/status",
    response_model=PlatformLibrarySuccessResponse,
    operation_id="changePlatformLibraryStatus",
    summary="Change platform library status",
    description=(
        "Locks and transitions a library between pending, active, and "
        "suspended while preserving all tenant history."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-STATUS"]},
)
def change_library_status(
    library_id: LibraryId,
    payload: PlatformLibraryStatusUpdate,
    request: Request,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PlatformLibrarySuccessResponse:
    library = platform_service.change_library_status(
        db,
        library_id,
        payload,
        current_user.id,
        audit_context=_audit_context(request),
    )
    return PlatformLibrarySuccessResponse(
        message="Library status updated successfully.",
        data=library,
    )


@router.patch(
    "/libraries/{libraryId}/owner",
    response_model=PlatformLibrarySuccessResponse,
    operation_id="assignPlatformLibraryOwner",
    summary="Assign a platform library owner",
    description=(
        "Assigns an eligible existing primary owner and preserves earlier "
        "membership history."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["PLATFORM-LIBRARY-OWNER-ASSIGN"]},
)
def assign_library_owner(
    library_id: LibraryId,
    payload: PlatformLibraryOwnerAssign,
    request: Request,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PlatformLibrarySuccessResponse:
    library = platform_service.assign_library_owner(
        db,
        library_id,
        payload,
        current_user.id,
        audit_context=_audit_context(request),
    )
    return PlatformLibrarySuccessResponse(
        message="Library owner assigned successfully.",
        data=library,
    )
