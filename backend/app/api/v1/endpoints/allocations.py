from __future__ import annotations

import uuid
import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
)
from app.models.enums import AllocationStatus
from app.schemas.allocation import (
    SeatAllocationCreate,
    SeatAllocationCreateResponse,
    SeatAllocationResponse,
    SeatAllocationStatusUpdate,
    SeatAvailabilityResponse,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
    error_responses,
)
from app.services import allocation as allocation_service
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
    end_date: Annotated[date | None, Query(alias="endDate")] = None,
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
        end_date=end_date or start_date,
        floor_id=floor_id,
        exclude_student_id=exclude_student_id,
    )
    return SuccessResponse(
        message="Seat availability fetched successfully.",
        data=availability,
    )


@router.get(
    "",
    response_model=PaginatedResponse[SeatAllocationResponse],
    operation_id="listSeatAllocations",
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["SEAT-ALLOCATION-LIST"]},
)
def list_seat_allocations(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    student_id: Annotated[
        uuid.UUID | None,
        Query(alias="studentId"),
    ] = None,
    seat_id: Annotated[
        uuid.UUID | None,
        Query(alias="seatId"),
    ] = None,
    shift_id: Annotated[
        uuid.UUID | None,
        Query(alias="shiftId"),
    ] = None,
    allocation_status: Annotated[
        AllocationStatus | None,
        Query(alias="status"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(alias="startDate"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(alias="endDate"),
    ] = None,
) -> PaginatedResponse[SeatAllocationResponse]:
    allocations, total = allocation_service.list_allocations(
        db,
        tenant.library_id,
        pagination,
        student_id=student_id,
        seat_id=seat_id,
        shift_id=shift_id,
        status=allocation_status,
        start_date=start_date,
        end_date=end_date,
    )
    return PaginatedResponse(
        message="Seat allocations fetched successfully.",
        data=allocations,
        meta=PaginationMeta(
            page=pagination.page,
            pageSize=pagination.page_size,
            totalItems=total,
            totalPages=math.ceil(total / pagination.page_size) if total else 0,
        ),
    )


@router.post(
    "",
    response_model=SuccessResponse[SeatAllocationCreateResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createSeatAllocation",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-ALLOCATION-CREATE"]},
)
def create_seat_allocation(
    payload: SeatAllocationCreate,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatAllocationCreateResponse]:
    result = allocation_service.create_allocations(
        db,
        tenant.library_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Seat allocation created successfully.",
        data=result,
    )


@router.patch(
    "/{allocation_id}/status",
    response_model=SuccessResponse[SeatAllocationResponse],
    operation_id="closeSeatAllocation",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-ALLOCATION-CLOSE"]},
)
def close_seat_allocation(
    allocation_id: uuid.UUID,
    payload: SeatAllocationStatusUpdate,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatAllocationResponse]:
    allocation = allocation_service.close_allocation(
        db,
        tenant.library_id,
        allocation_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message=f"Seat allocation {allocation.status.value}.",
        data=allocation,
    )
