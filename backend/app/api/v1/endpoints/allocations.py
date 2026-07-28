from __future__ import annotations

import uuid
import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
    CurrentStudent,
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
from app.schemas.student_portal import (
    StudentSeatAllocationsResponse,
    StudentSeatSummary,
    StudentAllocationItem,
)
from app.services import allocation as allocation_service
from app.services.audit import AuditContext


router = APIRouter(
    responses=error_responses(401, 403, 500),
)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get(
    "/me",
    response_model=SuccessResponse[StudentSeatAllocationsResponse],
    operation_id="getStudentSeatAllocations",
    summary="Get own seat allocations",
    description="Returns the authenticated student's active seat details and allocation history.",
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-SEAT-VIEW"]},
)
def get_own_seat_allocations(
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[StudentSeatAllocationsResponse]:
    from app.models.seat import SeatAllocation, Seat
    
    # Query all allocations belonging to the student
    all_allocs = db.scalars(
        select(SeatAllocation)
        .where(
            SeatAllocation.student_id == student_ctx.student_id,
            SeatAllocation.library_id == student_ctx.library_id,
        )
        .order_by(SeatAllocation.start_date.desc(), SeatAllocation.created_at.desc())
    ).all()
    
    today = date.today()
    active_items = []
    history_items = []
    
    for alloc in all_allocs:
        item = StudentAllocationItem(
            id=alloc.id,
            seat_id=alloc.seat_id,
            seat_number=alloc.seat_number_snapshot or (alloc.seat.seat_number if alloc.seat else ""),
            floor=alloc.floor_name_snapshot or (alloc.seat.floor.name if alloc.seat and alloc.seat.floor else ""),
            shift_id=alloc.shift_id,
            shift_name=alloc.shift_name,
            start_time=alloc.shift_start_time.isoformat()[:5],
            end_time=alloc.shift_end_time.isoformat()[:5],
            start_date=alloc.start_date,
            end_date=alloc.end_date,
            status=alloc.status,
            allocated_at=alloc.allocated_at,
        )
        if alloc.status == AllocationStatus.ACTIVE and alloc.end_date >= today:
            active_items.append(item)
        else:
            history_items.append(item)
            
    seat_summary = None
    if active_items:
        # Get details from the physical seat if available
        first_active_alloc = [a for a in all_allocs if a.status == AllocationStatus.ACTIVE and a.end_date >= today][0]
        seat = db.get(Seat, first_active_alloc.seat_id)
        if seat:
            seat_summary = StudentSeatSummary(
                id=seat.id,
                seat_number=seat.seat_number,
                floor=seat.floor.name if seat.floor else "",
                seat_type=seat.seat_type,
                notes=seat.notes,
            )
            
    return SuccessResponse(
        message="Seat allocations fetched successfully.",
        data=StudentSeatAllocationsResponse(
            seat=seat_summary,
            allocations=active_items,
            history=history_items,
        )
    )


@router.get(
    "/availability",
    response_model=SuccessResponse[SeatAvailabilityResponse],
    operation_id="getSeatAllocationAvailability",
    dependencies=[Depends(require_library_staff)],
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
    dependencies=[Depends(require_library_staff)],
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
    dependencies=[Depends(require_library_staff)],
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
    dependencies=[Depends(require_library_staff)],
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
