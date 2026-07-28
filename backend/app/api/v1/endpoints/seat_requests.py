from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
)
from app.models.enums import SeatRequestStatus
from app.schemas.common import PaginationMeta, SuccessResponse, error_responses
from app.schemas.seat_request import (
    SeatChangeRequestResponse,
    SeatRequestListResponse,
    SeatRequestReview,
)
from app.services import seat_request as service
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
    "",
    response_model=SeatRequestListResponse,
    operation_id="listOwnerSeatChangeRequests",
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
