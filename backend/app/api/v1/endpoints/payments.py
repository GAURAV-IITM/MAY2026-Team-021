from __future__ import annotations

import math
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import (
    CurrentTenant,
    DatabaseSession,
    Pagination,
    require_library_staff,
)
from app.models.enums import FeeStatus, PaymentMethod
from app.schemas.common import PaginationMeta, SuccessResponse, error_responses
from app.schemas.payment import (
    MonthlyFeeGenerationRequest,
    MonthlyFeeGenerationResponse,
    PaymentListResponse,
    PaymentTransactionCreate,
    PaymentTransactionRecordedResponse,
)
from app.schemas.receipt import (
    ReceiptDetail,
    ReceiptListResponse,
    ReceiptStatus,
    ReminderCreateRequest,
    WhatsAppReminderResponse,
)
from app.services import payment as payment_service
from app.services import receipt as receipt_service
from app.services import reminder as reminder_service
from app.services.receipt_document import render_receipt_pdf
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


@router.get(
    "/receipts",
    response_model=ReceiptListResponse,
    operation_id="listPaymentReceipts",
    summary="List payment receipts",
    description=(
        "Returns paginated immutable payment receipts belonging to the current "
        "library. Search and filters are applied by the server."
    ),
    responses=error_responses(422),
    openapi_extra={"x-user-stories": ["RECEIPT-LIST"]},
)
def list_receipts(
    db: DatabaseSession,
    tenant: CurrentTenant,
    pagination: Pagination,
    billing_month: Annotated[
        str | None,
        Query(
            alias="billingMonth",
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        ),
    ] = None,
    payment_method: Annotated[
        PaymentMethod | None,
        Query(alias="paymentMethod"),
    ] = None,
    student_id: Annotated[
        uuid.UUID | None,
        Query(alias="studentId"),
    ] = None,
    receipt_status: Annotated[
        ReceiptStatus | None,
        Query(alias="status"),
    ] = None,
    date_from: Annotated[
        date | None,
        Query(alias="dateFrom"),
    ] = None,
    date_to: Annotated[
        date | None,
        Query(alias="dateTo"),
    ] = None,
) -> ReceiptListResponse:
    result = receipt_service.list_receipts(
        db,
        tenant.library_id,
        pagination,
        billing_month=billing_month,
        payment_method=payment_method,
        student_id=student_id,
        status=receipt_status,
        date_from=date_from,
        date_to=date_to,
    )
    return ReceiptListResponse(
        message="Receipts fetched successfully.",
        data=result.receipts,
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
    )


@router.get(
    "/receipts/{receipt_id}",
    response_model=SuccessResponse[ReceiptDetail],
    operation_id="getPaymentReceipt",
    summary="Get a payment receipt",
    description=(
        "Returns the immutable snapshot used for receipt preview. Receipts "
        "outside the current library are hidden as not found."
    ),
    responses=error_responses(404),
    openapi_extra={"x-user-stories": ["RECEIPT-PREVIEW"]},
)
def get_receipt(
    receipt_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[ReceiptDetail]:
    return SuccessResponse(
        message="Receipt fetched successfully.",
        data=receipt_service.get_receipt(
            db,
            tenant.library_id,
            receipt_id,
        ),
    )


@router.get(
    "/receipts/{receipt_id}/download",
    response_class=Response,
    operation_id="downloadPaymentReceipt",
    summary="Download a payment receipt",
    description=(
        "Returns an authenticated PDF generated from the same immutable "
        "snapshot used by receipt preview."
    ),
    responses={
        200: {
            "description": "Receipt PDF.",
            "content": {"application/pdf": {}},
            "headers": {
                "Content-Disposition": {
                    "description": "Suggested receipt filename.",
                    "schema": {"type": "string"},
                }
            },
        },
        **error_responses(404, 500),
    },
    openapi_extra={"x-user-stories": ["RECEIPT-DOWNLOAD"]},
)
def download_receipt(
    receipt_id: uuid.UUID,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> Response:
    receipt = receipt_service.get_receipt(
        db,
        tenant.library_id,
        receipt_id,
    )
    document = render_receipt_pdf(receipt)
    return Response(
        content=document,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="receipt-{receipt.receipt_number}.pdf"'
            )
        },
    )


@router.post(
    "/{fee_record_id}/reminders",
    response_model=SuccessResponse[WhatsAppReminderResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="createPaymentReminder",
    summary="Create a WhatsApp payment reminder",
    description=(
        "Validates the current outstanding balance and student phone, records "
        "an auditable link-generation attempt, then returns a wa.me URL. This "
        "does not claim the message was sent or delivered."
    ),
    responses=error_responses(404, 409, 422),
    openapi_extra={"x-user-stories": ["PAYMENT-WHATSAPP-REMINDER"]},
)
def create_payment_reminder(
    fee_record_id: uuid.UUID,
    payload: ReminderCreateRequest,
    request: Request,
    db: DatabaseSession,
    tenant: CurrentTenant,
) -> SuccessResponse[WhatsAppReminderResponse]:
    result = reminder_service.create_whatsapp_reminder(
        db,
        tenant.library_id,
        fee_record_id,
        payload,
        tenant.user.id,
        audit_context=_audit_context(request),
    )
    return SuccessResponse(
        message="Reminder attempt recorded and WhatsApp link generated.",
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
