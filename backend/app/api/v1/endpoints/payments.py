from __future__ import annotations

import math
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
)
from app.models.enums import FeeStatus
from app.schemas.common import PaginationMeta, SuccessResponse, error_responses
from app.schemas.payment import (
    MonthlyFeeGenerationRequest,
    MonthlyFeeGenerationResponse,
    PaymentListResponse,
    PaymentTransactionCreate,
    PaymentTransactionRecordedResponse,
)
from app.services import payment as payment_service
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
    response_model=PaymentListResponse,
    operation_id="listPayments",
    summary="List monthly fee records",
    description=(
        "Returns tenant-scoped monthly fee records with server-calculated "
        "payment totals, balances, statuses, and transactions."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["PAYMENT-LIST", "PAYMENT-HISTORY"]},
)
def list_payments(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    month: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    ] = None,
    payment_status: Annotated[
        FeeStatus | None,
        Query(alias="status"),
    ] = None,
    student_id: Annotated[
        uuid.UUID | None,
        Query(alias="studentId"),
    ] = None,
    due_date_from: Annotated[
        date | None,
        Query(alias="dueDateFrom"),
    ] = None,
    due_date_to: Annotated[
        date | None,
        Query(alias="dueDateTo"),
    ] = None,
    has_transactions: Annotated[
        bool | None,
        Query(alias="hasTransactions"),
    ] = None,
) -> PaymentListResponse:
    result = payment_service.list_payments(
        db,
        tenant.library_id,
        pagination,
        month=month,
        status=payment_status,
        student_id=student_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        has_transactions=has_transactions,
    )
    return PaymentListResponse(
        message="Payments fetched successfully.",
        data=result.payments,
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


@router.post(
    "/monthly-generation",
    response_model=SuccessResponse[MonthlyFeeGenerationResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="generateMonthlyFees",
    summary="Generate monthly fee records",
    description=(
        "Idempotently creates one fee record for each eligible active student. "
        "Student eligibility, fee amounts, due dates, and initial status are "
        "derived by the server."
    ),
    responses=error_responses(409, 422),
    openapi_extra={"x-user-stories": ["MONTHLY-FEE-GENERATION"]},
)
def generate_monthly_fees(
    payload: MonthlyFeeGenerationRequest,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[MonthlyFeeGenerationResponse]:
    result = payment_service.generate_monthly_fees(
        db,
        tenant.library_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Monthly fee generation completed.",
        data=result,
    )


@router.post(
    "/{fee_record_id}/transactions",
    response_model=SuccessResponse[PaymentTransactionRecordedResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="recordPaymentTransaction",
    summary="Record a payment transaction",
    description=(
        "Records an immutable payment transaction and recalculates the fee "
        "record's paid amount, balance, and status on the server."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["PAYMENT-RECORD"]},
)
def record_payment_transaction(
    fee_record_id: uuid.UUID,
    payload: PaymentTransactionCreate,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[PaymentTransactionRecordedResponse]:
    result = payment_service.record_payment(
        db,
        tenant.library_id,
        fee_record_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Payment recorded successfully.",
        data=result,
    )
