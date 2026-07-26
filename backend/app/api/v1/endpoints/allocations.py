from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentTenant, DatabaseSession, require_library_staff
from app.schemas.allocation import SeatAvailabilityResponse
from app.schemas.common import SuccessResponse, error_responses
from app.services import allocation as allocation_service


router = APIRouter(
    dependencies=[Depends(require_library_staff)],
    responses=error_responses(401, 403, 500),
)


@router.get(
    "/availability",
    response_model=SuccessResponse[SeatAvailabilityResponse],
    operation_id="getSeatAllocationAvailability",
    responses=error_responses(404, 422),
    openapi_extra={
        "x-user-stories": [
            "STUDENT-REGISTER-SEAT",
            "SEAT-AVAILABILITY",
        ]
    },
)
def get_seat_allocation_availability(
    db: DatabaseSession,
    tenant: CurrentTenant,
    shift_ids: Annotated[
        list[uuid.UUID],
        Query(alias="shiftId", min_length=1),
    ],
    start_date: Annotated[date, Query(alias="startDate")],
    end_date: Annotated[date, Query(alias="endDate")],
    floor_id: Annotated[
        uuid.UUID | None,
        Query(alias="floorId"),
    ] = None,
    exclude_student_id: Annotated[
        uuid.UUID | None,
        Query(alias="excludeStudentId"),
    ] = None,
) -> SuccessResponse[SeatAvailabilityResponse]:
    availability = allocation_service.get_seat_availability(
        db,
        tenant.library_id,
        shift_ids=shift_ids,
        start_date=start_date,
        end_date=end_date,
        floor_id=floor_id,
        exclude_student_id=exclude_student_id,
    )
    return SuccessResponse(
        message="Seat availability fetched successfully.",
        data=availability,
    )
