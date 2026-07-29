from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from sqlalchemy import select

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
    CurrentStudent,
)
from app.models.enums import SeatRequestStatus
from app.schemas.common import PaginationMeta, SuccessResponse, error_responses
from app.schemas.seat_request import (
    SeatChangeRequestResponse,
    SeatRequestListResponse,
    SeatRequestReview,
)
from app.schemas.student_portal import (
    StudentSeatRequestCreate,
    StudentSeatRequestsResponse,
    StudentSeatRequestListItem,
)
from app.services import seat_request as service
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
    response_model=SuccessResponse[StudentSeatRequestsResponse],
    operation_id="getStudentSeatRequests",
    summary="Get own seat-change requests",
    description="Returns the authenticated student's own requests and active library shifts.",
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-REQUESTS-VIEW"]},
)
def get_own_requests(
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[StudentSeatRequestsResponse]:
    from app.models.seat import SeatChangeRequest, Shift
    
    # Query all requests belonging to the student
    all_reqs = db.scalars(
        select(SeatChangeRequest)
        .where(
            SeatChangeRequest.student_id == student_ctx.student_id,
            SeatChangeRequest.library_id == student_ctx.library_id,
        )
        .order_by(SeatChangeRequest.submitted_at.desc())
    ).all()
    
    req_items = [
        StudentSeatRequestListItem(
            id=req.id,
            student_id=req.student_id,
            student_name=f"{req.student.first_name} {req.student.last_name}".strip(),
            student_email=req.student.email or "",
            library_id=req.library_id,
            library_name=student_ctx.membership.library.name if student_ctx.membership and student_ctx.membership.library else "",
            current_seat_number=(
                req.current_allocation.seat_number_snapshot or 
                (req.current_allocation.seat.seat_number if req.current_allocation.seat else None)
            ) if req.current_allocation else None,
            preferred_seat_number=req.preferred_seat.seat_number if req.preferred_seat else None,
            preferred_floor=req.preferred_floor.name if req.preferred_floor else None,
            preferred_shift_id=req.preferred_shift_id,
            preferred_shift_name=req.preferred_shift.name,
            reason=req.reason,
            status=req.status,
            admin_note=req.admin_note,
            submitted_at=req.submitted_at,
            resolved_at=req.resolved_at,
            reviewed_by={"id": req.reviewed_by.id, "name": req.reviewed_by.full_name} if req.reviewed_by else None,
        )
        for req in all_reqs
    ]
    
    # Query all active shifts in the library
    active_shifts = db.scalars(
        select(Shift)
        .where(
            Shift.library_id == student_ctx.library_id,
            Shift.is_active.is_(True),
            Shift.deleted_at.is_(None),
        )
        .order_by(Shift.start_time)
    ).all()
    
    shift_items = [
        {
            "id": str(s.id),
            "name": s.name,
            "startTime": s.start_time.strftime("%H:%M"),
            "endTime": s.end_time.strftime("%H:%M"),
        }
        for s in active_shifts
    ]
    
    return SuccessResponse(
        message="Seat change requests fetched successfully.",
        data=StudentSeatRequestsResponse(
            requests=req_items,
            shifts=shift_items,
        ),
    )


@router.post(
    "/me",
    response_model=SuccessResponse[SeatChangeRequestResponse],
    operation_id="createStudentSeatRequest",
    summary="Submit a seat-change request",
    description="Submits a new pending seat or shift change request.",
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-REQUEST-SUBMIT"]},
)
def submit_seat_request(
    payload: StudentSeatRequestCreate,
    request: Request,
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[SeatChangeRequestResponse]:
    result = service.create_seat_request(
        db,
        student_ctx.library_id,
        student_ctx.student_id,
        payload,
        student_ctx.student.user_id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Seat change request submitted successfully.",
        data=result,
    )


@router.patch(
    "/me/{request_id}/cancel",
    response_model=SuccessResponse[SeatChangeRequestResponse],
    operation_id="cancelStudentSeatRequest",
    summary="Cancel a seat-change request",
    description="Cancels a pending seat-change request.",
    responses=error_responses(404, 409),
    openapi_extra={"x-user-stories": ["STUDENT-PORTAL-REQUEST-CANCEL"]},
)
def cancel_seat_request(
    request_id: uuid.UUID,
    request: Request,
    db: DatabaseSession,
    student_ctx: CurrentStudent,
) -> SuccessResponse[SeatChangeRequestResponse]:
    result = service.cancel_seat_request(
        db,
        student_ctx.library_id,
        request_id,
        student_ctx.student_id,
        student_ctx.student.user_id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Seat change request cancelled successfully.",
        data=result,
    )


@router.get(
    "",
    response_model=SeatRequestListResponse,
    operation_id="listOwnerSeatChangeRequests",
    dependencies=[Depends(require_library_staff)],
    summary="List seat-change requests",
    description=(
        "Returns tenant-scoped student seat-change request history for "
        "Library Owners and authorised staff."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["SEAT-REQUEST-LIST"]},
)
def list_requests(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    request_status: Annotated[
        SeatRequestStatus | None,
        Query(alias="status"),
    ] = None,
    student_id: Annotated[
        uuid.UUID | None,
        Query(alias="studentId"),
    ] = None,
    preferred_floor_id: Annotated[
        uuid.UUID | None,
        Query(alias="preferredFloorId"),
    ] = None,
    preferred_shift_id: Annotated[
        uuid.UUID | None,
        Query(alias="preferredShiftId"),
    ] = None,
) -> SeatRequestListResponse:
    result = service.list_requests(
        db,
        tenant.library_id,
        pagination,
        status=request_status,
        student_id=student_id,
        preferred_floor_id=preferred_floor_id,
        preferred_shift_id=preferred_shift_id,
    )
    return SeatRequestListResponse(
        message="Seat-change requests fetched successfully.",
        data=result.requests,
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


@router.patch(
    "/{request_id}/review",
    response_model=SuccessResponse[SeatChangeRequestResponse],
    operation_id="reviewOwnerSeatChangeRequest",
    dependencies=[Depends(require_library_staff)],
    summary="Review a seat-change request",
    description=(
        "Records one final approval or rejection. Approval does not create, "
        "cancel, reserve, or transfer any seat allocation."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["SEAT-REQUEST-REVIEW"]},
)
def review_request(
    request_id: uuid.UUID,
    payload: SeatRequestReview,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[SeatChangeRequestResponse]:
    reviewed = service.review_request(
        db,
        tenant.library_id,
        request_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message=(
            "Seat-change request approved. No seat allocation was changed."
            if reviewed.status == SeatRequestStatus.APPROVED
            else "Seat-change request rejected."
        ),
        data=reviewed,
    )
