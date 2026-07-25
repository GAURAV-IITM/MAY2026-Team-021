"""Library settings endpoints."""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentTenant, DatabaseSession, require_library_owner
from app.schemas.common import SuccessResponse, error_responses
from app.schemas.library import LibrarySettingsResponse, LibrarySettingsUpdate
from app.services import library as library_service


router = APIRouter(
    dependencies=[Depends(require_library_owner)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "/library",
    response_model=SuccessResponse[LibrarySettingsResponse],
    operation_id="getLibrarySettings",
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["LIBRARY-SETTINGS-READ"]},
)
def get_library_settings(
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[LibrarySettingsResponse]:
    return SuccessResponse(
        message="Library settings fetched successfully.",
        data=library_service.get_settings(db, tenant.library_id),
    )


@router.patch(
    "/library",
    response_model=SuccessResponse[LibrarySettingsResponse],
    operation_id="updateLibrarySettings",
    responses=error_responses(404, 422),
    openapi_extra={"x-user-stories": ["LIBRARY-SETTINGS-UPDATE"]},
)
def update_library_settings(
    payload: LibrarySettingsUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[LibrarySettingsResponse]:
    return SuccessResponse(
        message="Library settings updated successfully.",
        data=library_service.update_settings(
            db,
            tenant.library_id,
            payload,
        ),
    )
