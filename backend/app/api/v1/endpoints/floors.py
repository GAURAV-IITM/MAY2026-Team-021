"""Physical floor management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentTenant, DatabaseSession, require_library_owner
from app.schemas.common import MessageResponse, SuccessResponse, error_responses
from app.schemas.seat import FloorCreate, FloorResponse, FloorUpdate
from app.services import seat as seat_service


router = APIRouter(
    dependencies=[Depends(require_library_owner)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "",
    response_model=SuccessResponse[list[FloorResponse]],
    operation_id="listFloors",
    openapi_extra={"x-user-stories": ["FLOOR-LIST"]},
)
def list_floors(
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[list[FloorResponse]]:
    return SuccessResponse(
        message="Floors fetched successfully.",
        data=seat_service.list_floors(db, tenant.library_id),
    )


@router.post(
    "",
    response_model=SuccessResponse[FloorResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createFloor",
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["FLOOR-CREATE"]},
)
def create_floor(
    payload: FloorCreate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[FloorResponse]:
    return SuccessResponse(
        message="Floor created successfully.",
        data=seat_service.create_floor(db, tenant.library_id, payload),
    )


@router.patch(
    "/{floor_id}",
    response_model=SuccessResponse[FloorResponse],
    operation_id="updateFloor",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["FLOOR-UPDATE"]},
)
def update_floor(
    floor_id: uuid.UUID,
    payload: FloorUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[FloorResponse]:
    return SuccessResponse(
        message="Floor updated successfully.",
        data=seat_service.update_floor(
            db,
            tenant.library_id,
            floor_id,
            payload,
        ),
    )


@router.delete(
    "/{floor_id}",
    response_model=MessageResponse,
    operation_id="deleteFloor",
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["FLOOR-DELETE"]},
)
def delete_floor(
    floor_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> MessageResponse:
    seat_service.delete_floor(db, tenant.library_id, floor_id)
    return MessageResponse(message="Floor deleted successfully.")
