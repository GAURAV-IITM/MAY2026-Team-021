"""Study shift management and selection validation endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentTenant, DatabaseSession, require_library_owner
from app.schemas.common import MessageResponse, SuccessResponse, error_responses
from app.schemas.seat import (
    ShiftCreate,
    ShiftResponse,
    ShiftSelectionResult,
    ShiftSelectionValidation,
    ShiftStatusUpdate,
    ShiftUpdate,
)
from app.services import seat as seat_service


router = APIRouter(
    dependencies=[Depends(require_library_owner)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "",
    response_model=SuccessResponse[list[ShiftResponse]],
    operation_id="listShifts",
    openapi_extra={"x-user-stories": ["SHIFT-LIST"]},
)
def list_shifts(
    db: DatabaseSession,
    tenant: CurrentTenant,
    include_inactive: Annotated[
        bool,
        Query(alias="includeInactive"),
    ] = True,
) -> SuccessResponse[list[ShiftResponse]]:
    return SuccessResponse(
        message="Shifts fetched successfully.",
        data=seat_service.list_shifts(
            db,
            tenant.library_id,
            include_inactive=include_inactive,
        ),
    )


@router.post(
    "",
    response_model=SuccessResponse[ShiftResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createShift",
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["SHIFT-CREATE"]},
)
def create_shift(
    payload: ShiftCreate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ShiftResponse]:
    return SuccessResponse(
        message="Shift created successfully.",
        data=seat_service.create_shift(db, tenant.library_id, payload),
    )


@router.post(
    "/validate-selection",
    response_model=SuccessResponse[ShiftSelectionResult],
    operation_id="validateShiftSelection",
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["SHIFT-VALIDATE-SELECTION"]},
)
def validate_shift_selection(
    payload: ShiftSelectionValidation,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ShiftSelectionResult]:
    result = seat_service.validate_shift_selection(
        db,
        tenant.library_id,
        payload.shift_ids,
    )
    return SuccessResponse(
        message=(
            "Selected shifts do not overlap."
            if result.valid
            else "Selected shifts contain overlapping time ranges."
        ),
        data=result,
    )


@router.patch(
    "/{shift_id}",
    response_model=SuccessResponse[ShiftResponse],
    operation_id="updateShift",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SHIFT-UPDATE"]},
)
def update_shift(
    shift_id: uuid.UUID,
    payload: ShiftUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ShiftResponse]:
    return SuccessResponse(
        message="Shift updated successfully.",
        data=seat_service.update_shift(
            db,
            tenant.library_id,
            shift_id,
            payload,
        ),
    )


@router.patch(
    "/{shift_id}/status",
    response_model=SuccessResponse[ShiftResponse],
    operation_id="changeShiftStatus",
    responses=error_responses(404, 422),
    openapi_extra={"x-user-stories": ["SHIFT-STATUS"]},
)
def change_shift_status(
    shift_id: uuid.UUID,
    payload: ShiftStatusUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ShiftResponse]:
    return SuccessResponse(
        message="Shift status updated successfully.",
        data=seat_service.update_shift(
            db,
            tenant.library_id,
            shift_id,
            ShiftUpdate(is_enabled=payload.is_enabled),
        ),
    )


@router.delete(
    "/{shift_id}",
    response_model=MessageResponse,
    operation_id="deleteShift",
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["SHIFT-DELETE"]},
)
def delete_shift(
    shift_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> MessageResponse:
    seat_service.delete_shift(db, tenant.library_id, shift_id)
    return MessageResponse(message="Shift deleted successfully.")
