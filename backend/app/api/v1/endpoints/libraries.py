
# TODO: Add library registration and membership routes.
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    require_library_owner,
)
from app.schemas.common import (
    SuccessResponse,
    error_responses,
)
from app.schemas.library import (
    LibraryProfileResponse,
    LibraryProfileUpdate,
)
from app.services import library as library_service


router = APIRouter(
    dependencies=[Depends(require_library_owner)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "/profile",
    response_model=SuccessResponse[LibraryProfileResponse],
    operation_id="getLibraryProfile",
    summary="Get library owner profile",
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["LIBRARY-PROFILE-VIEW"]},
)
def get_library_profile(
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[LibraryProfileResponse]:
    return SuccessResponse(
        message="Library profile fetched successfully.",
        data=library_service.get_profile(
            db,
            tenant.library_id,
        ),
    )


@router.patch(
    "/profile",
    response_model=SuccessResponse[LibraryProfileResponse],
    operation_id="updateLibraryProfile",
    summary="Update library owner profile",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["LIBRARY-PROFILE-UPDATE"]},
)
def update_library_profile(
    payload: LibraryProfileUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[LibraryProfileResponse]:
    return SuccessResponse(
        message="Library profile updated successfully.",
        data=library_service.update_profile(
            db,
            tenant.library_id,
            payload,
            tenant.user.id,
        ),
    )