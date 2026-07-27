"""Automatic receipt issuance and tenant-safe receipt access."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.models.enums import PaymentMethod, PaymentTransactionStatus
from app.models.payment import FeeRecord, PaymentTransaction, Receipt
from app.repositories import receipt as repository
from app.schemas.common import PaginationParams
from app.schemas.receipt import (
    ReceiptActorSummary,
    ReceiptDetail,
    ReceiptFeeSummary,
    ReceiptLibrarySummary,
    ReceiptListItem,
    ReceiptPaymentSummary,
    ReceiptStatus,
    ReceiptStudentSummary,
)
from app.services.audit import AuditContext, write_audit_log


ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class ReceiptListResult:
    receipts: list[ReceiptListItem]
    total: int


def _money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def _address(library) -> str | None:
    parts = [
        library.address_line,
        library.city,
        library.state,
        library.postal_code,
    ]
    value = ", ".join(str(part).strip() for part in parts if part)
    return value or None


def _receipt_number(prefix: str, issued_at: datetime, receipt_id: uuid.UUID) -> str:
    safe_prefix = re.sub(r"[^A-Za-z0-9]", "", prefix).upper() or "REC"
    return f"{safe_prefix}-{issued_at.year}-{receipt_id.hex.upper()}"


def _snapshot(
    *,
    library,
    fee: FeeRecord,
    transaction: PaymentTransaction,
    paid_before: Decimal,
    paid_after: Decimal,
) -> dict[str, object]:
    student = fee.student
    actor = transaction.recorded_by
    return {
        "currency": "INR",
        "library": {
            "id": str(library.id),
            "name": library.name,
            "address": _address(library),
            "phone": library.contact_phone,
            "email": library.contact_email,
        },
        "student": {
            "id": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "enrollmentNumber": student.enrollment_number,
        },
        "fee": {
            "id": str(fee.id),
            "billingMonth": fee.billing_month.strftime("%Y-%m"),
            "dueDate": fee.due_date.isoformat(),
            "totalAmount": str(_money(fee.total_amount)),
            "previouslyPaidAmount": str(_money(paid_before)),
            "paymentAmount": str(_money(transaction.amount)),
            "remainingBalance": str(
                max(_money(fee.total_amount) - _money(paid_after), ZERO)
            ),
            "paymentStatus": fee.status.value,
        },
        "payment": {
            "id": str(transaction.id),
            "amount": str(_money(transaction.amount)),
            "method": transaction.method.value,
            "referenceNumber": transaction.reference_number,
            "paidAt": transaction.paid_at.isoformat(),
            "recordedBy": (
                {"id": str(actor.id), "name": actor.full_name}
                if actor
                else None
            ),
            "notes": transaction.notes,
        },
    }


def issue_receipt(
    db: Session,
    *,
    library_id: uuid.UUID,
    fee: FeeRecord,
    transaction: PaymentTransaction,
    paid_before: Decimal,
    paid_after: Decimal,
    actor_user_id: uuid.UUID,
    audit_context: AuditContext | None = None,
) -> Receipt:
    if transaction.status != PaymentTransactionStatus.COMPLETED:
        raise BusinessRuleError(
            "Only completed payment transactions can receive a receipt.",
            code="RECEIPT_TRANSACTION_NOT_COMPLETED",
        )
    existing = repository.get_by_transaction(
        db,
        library_id,
        transaction.id,
    )
    if existing is not None:
        return existing

    library = repository.get_library(db, library_id)
    if library is None:
        raise ResourceNotFoundError(
            "Library not found.",
            code="LIBRARY_NOT_FOUND",
        )
    issued_at = datetime.now(timezone.utc)
    receipt_id = uuid.uuid4()
    prefix = library.settings.receipt_prefix if library.settings else "REC"
    receipt = Receipt(
        id=receipt_id,
        library_id=library_id,
        student_id=fee.student_id,
        transaction_id=transaction.id,
        receipt_number=_receipt_number(prefix, issued_at, receipt_id),
        issued_at=issued_at,
        snapshot=_snapshot(
            library=library,
            fee=fee,
            transaction=transaction,
            paid_before=paid_before,
            paid_after=paid_after,
        ),
    )
    receipt.transaction = transaction
    repository.add(db, receipt)
    write_audit_log(
        db,
        library_id=library_id,
        actor_user_id=actor_user_id,
        action="receipt.issued",
        entity_type="receipt",
        entity_id=str(receipt.id),
        new_values={
            "receiptNumber": receipt.receipt_number,
            "paymentTransactionId": str(transaction.id),
            "feeRecordId": str(fee.id),
            "studentId": str(fee.student_id),
            "amount": str(_money(transaction.amount)),
        },
        request_context=audit_context,
    )
    return receipt


def _status(receipt: Receipt) -> ReceiptStatus:
    return (
        ReceiptStatus.VOIDED
        if receipt.voided_at is not None
        else ReceiptStatus.ISSUED
    )


def receipt_list_item(receipt: Receipt) -> ReceiptListItem:
    snapshot = receipt.snapshot
    student = snapshot["student"]
    fee = snapshot["fee"]
    payment = snapshot["payment"]
    return ReceiptListItem(
        id=receipt.id,
        receipt_number=receipt.receipt_number,
        student=ReceiptStudentSummary(
            id=student["id"],
            name=student["name"],
            enrollment_number=student["enrollmentNumber"],
        ),
        fee_record_id=fee["id"],
        payment_transaction_id=payment["id"],
        billing_month=fee["billingMonth"],
        amount=payment["amount"],
        payment_method=payment["method"],
        payment_reference=payment["referenceNumber"],
        paid_at=payment["paidAt"],
        issued_at=receipt.issued_at,
        status=_status(receipt),
        currency=snapshot.get("currency", "INR"),
        download_available=True,
    )


def receipt_detail(receipt: Receipt) -> ReceiptDetail:
    snapshot = receipt.snapshot
    library = snapshot["library"]
    student = snapshot["student"]
    fee = snapshot["fee"]
    payment = snapshot["payment"]
    actor = payment.get("recordedBy")
    return ReceiptDetail(
        id=receipt.id,
        receipt_number=receipt.receipt_number,
        status=_status(receipt),
        issued_at=receipt.issued_at,
        currency=snapshot.get("currency", "INR"),
        library=ReceiptLibrarySummary(
            id=library["id"],
            name=library["name"],
            address=library.get("address"),
            phone=library.get("phone"),
            email=library["email"],
        ),
        student=ReceiptStudentSummary(
            id=student["id"],
            name=student["name"],
            enrollment_number=student["enrollmentNumber"],
        ),
        fee=ReceiptFeeSummary(
            id=fee["id"],
            billing_month=fee["billingMonth"],
            due_date=fee["dueDate"],
            total_amount=fee["totalAmount"],
            previously_paid_amount=fee["previouslyPaidAmount"],
            payment_amount=fee["paymentAmount"],
            remaining_balance=fee["remainingBalance"],
            payment_status=fee["paymentStatus"],
        ),
        payment=ReceiptPaymentSummary(
            id=payment["id"],
            amount=payment["amount"],
            method=payment["method"],
            reference_number=payment.get("referenceNumber"),
            paid_at=payment["paidAt"],
            recorded_by=(
                ReceiptActorSummary(id=actor["id"], name=actor["name"])
                if actor
                else None
            ),
            notes=payment.get("notes"),
        ),
    )


def list_receipts(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    billing_month: str | None = None,
    payment_method: PaymentMethod | None = None,
    student_id: uuid.UUID | None = None,
    status: ReceiptStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReceiptListResult:
    if date_from and date_to and date_to < date_from:
        raise BusinessRuleError(
            "Receipt date end cannot be earlier than receipt date start.",
            code="RECEIPT_DATE_RANGE_INVALID",
        )
    month = (
        date.fromisoformat(f"{billing_month}-01")
        if billing_month
        else None
    )
    records, total = repository.list_receipts(
        db,
        library_id,
        pagination,
        billing_month=month,
        payment_method=payment_method,
        student_id=student_id,
        receipt_status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return ReceiptListResult(
        receipts=[receipt_list_item(record) for record in records],
        total=total,
    )


def get_receipt(
    db: Session,
    library_id: uuid.UUID,
    receipt_id: uuid.UUID,
) -> ReceiptDetail:
    receipt = repository.get_tenant_receipt(db, library_id, receipt_id)
    if receipt is None:
        raise ResourceNotFoundError(
            "Receipt not found.",
            code="RECEIPT_NOT_FOUND",
        )
    return receipt_detail(receipt)
