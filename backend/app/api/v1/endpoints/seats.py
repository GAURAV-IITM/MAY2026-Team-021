"""Physical seat CRUD and bulk status endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentTenant, DatabaseSession, require_library_owner
from app.models.enums import SeatOperationalStatus
from app.schemas.common import SuccessResponse, error_responses
from app.schemas.seat import (
    BulkSeatDeleteRequest,
    BulkSeatResult,
    BulkSeatStatusUpdate,
    SeatCreate,
    SeatListResponse,
    SeatResponse,
    SeatStatusUpdate,
    SeatUpdate,
)
from app.services import seat as seat_service


router = APIRouter(
    dependencies=[Depends(require_library_owner)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "",
    response_model=SuccessResponse[SeatListResponse],
    operation_id="listSeats",
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["SEAT-LIST"]},
)
def list_seats(
    db: DatabaseSession,
    tenant: CurrentTenant,
    search: Annotated[str | None, Query(max_length=200)] = None,
    floor_id: Annotated[uuid.UUID | None, Query(alias="floorId")] = None,
    seat_status: Annotated[
        SeatOperationalStatus | None,
        Query(alias="status"),
    ] = None,
) -> SuccessResponse[SeatListResponse]:
    seats, shifts = seat_service.list_seats(
        db,
        tenant.library_id,
        search=search,
        floor_id=floor_id,
        status=seat_status,
    )
    return SuccessResponse(
        message="Seats fetched successfully.",
        data=SeatListResponse(seats=seats, shifts=shifts),
    )


@router.post(
    "",
    response_model=SuccessResponse[SeatResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createSeat",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-CREATE"]},
)
def create_seat(
    payload: SeatCreate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatResponse]:
    return SuccessResponse(
        message="Seat created successfully.",
        data=seat_service.create_seat(
            db,
            tenant.library_id,
            payload,
            tenant.user.id,
        ),
    )


@router.patch(
    "/bulk/status",
    response_model=SuccessResponse[BulkSeatResult],
    operation_id="bulkChangeSeatStatus",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-BULK-STATUS"]},
)
def bulk_change_status(
    payload: BulkSeatStatusUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[BulkSeatResult]:
    result = seat_service.bulk_change_status(
        db,
        tenant.library_id,
        payload.seat_ids,
        SeatStatusUpdate(status=payload.status, reason=payload.reason),
        tenant.user.id,
    )
    return SuccessResponse(
        message="Selected seat statuses updated successfully.",
        data=result,
    )


@router.post(
    "/bulk/delete",
    response_model=SuccessResponse[BulkSeatResult],
    operation_id="bulkDeleteSeats",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-BULK-DELETE"]},
)
def bulk_delete_seats(
    payload: BulkSeatDeleteRequest,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[BulkSeatResult]:
    deleted_ids = seat_service.delete_seats(
        db,
        tenant.library_id,
        payload.seat_ids,
    )
    return SuccessResponse(
        message="Selected seats deleted successfully.",
        data=BulkSeatResult(deleted_seat_ids=deleted_ids),
    )


@router.get(
    "/{seat_id}",
    response_model=SuccessResponse[SeatResponse],
    operation_id="getSeat",
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["SEAT-DETAIL"]},
)
def get_seat(
    seat_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatResponse]:
    return SuccessResponse(
        message="Seat fetched successfully.",
        data=seat_service.get_seat(db, tenant.library_id, seat_id),
    )


@router.patch(
    "/{seat_id}",
    response_model=SuccessResponse[SeatResponse],
    operation_id="updateSeat",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-UPDATE"]},
)
def update_seat(
    seat_id: uuid.UUID,
    payload: SeatUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatResponse]:
    return SuccessResponse(
        message="Seat updated successfully.",
        data=seat_service.update_seat(
            db,
            tenant.library_id,
            seat_id,
            payload,
            tenant.user.id,
        ),
    )


@router.patch(
    "/{seat_id}/status",
    response_model=SuccessResponse[SeatResponse],
    operation_id="changeSeatStatus",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-STATUS"]},
)
def change_seat_status(
    seat_id: uuid.UUID,
    payload: SeatStatusUpdate,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatResponse]:
    return SuccessResponse(
        message="Seat status updated successfully.",
        data=seat_service.change_seat_status(
            db,
            tenant.library_id,
            seat_id,
            payload,
            tenant.user.id,
        ),
    )


@router.delete(
    "/{seat_id}",
    response_model=SuccessResponse[BulkSeatResult],
    operation_id="deleteSeat",
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["SEAT-DELETE"]},
)
def delete_seat(
    seat_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[BulkSeatResult]:
    deleted_ids = seat_service.delete_seats(db, tenant.library_id, [seat_id])
    return SuccessResponse(
        message="Seat deleted successfully.",
        data=BulkSeatResult(deleted_seat_ids=deleted_ids),
    )
