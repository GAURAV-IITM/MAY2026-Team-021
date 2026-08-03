"""Tenant-scoped receipt persistence and query helpers."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import PaymentMethod, PaymentTransactionStatus
from app.models.library import Library
from app.models.payment import FeeRecord, PaymentTransaction, Receipt
from app.models.student import Student
from app.schemas.common import PaginationParams
from app.schemas.receipt import ReceiptStatus


SORT_COLUMNS = {
    "createdAt": Receipt.created_at,
    "issuedAt": Receipt.issued_at,
    "receiptNumber": Receipt.receipt_number,
    "billingMonth": FeeRecord.billing_month,
    "amount": PaymentTransaction.amount,
    "paidAt": PaymentTransaction.paid_at,
    "studentName": Student.first_name,
}


def get_library(db: Session, library_id: uuid.UUID) -> Library | None:
    return db.scalar(
        select(Library)
        .options(joinedload(Library.settings))
        .where(
            Library.id == library_id,
            Library.deleted_at.is_(None),
        )
    )


def get_by_transaction(
    db: Session,
    library_id: uuid.UUID,
    transaction_id: uuid.UUID,
) -> Receipt | None:
    return db.scalar(
        select(Receipt).where(
            Receipt.library_id == library_id,
            Receipt.transaction_id == transaction_id,
        )
    )


def add(db: Session, receipt: Receipt) -> Receipt:
    db.add(receipt)
    db.flush()
    return receipt


def _conditions(
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    billing_month: date | None,
    payment_method: PaymentMethod | None,
    student_id: uuid.UUID | None,
    receipt_status: ReceiptStatus | None,
    date_from: date | None,
    date_to: date | None,
) -> list[object]:
    conditions: list[object] = [
        Receipt.library_id == library_id,
        PaymentTransaction.library_id == library_id,
        PaymentTransaction.status == PaymentTransactionStatus.COMPLETED,
        FeeRecord.library_id == library_id,
        Student.library_id == library_id,
    ]
    if billing_month is not None:
        conditions.append(FeeRecord.billing_month == billing_month)
    if payment_method is not None:
        conditions.append(PaymentTransaction.method == payment_method)
    if student_id is not None:
        conditions.append(Receipt.student_id == student_id)
    if receipt_status == ReceiptStatus.ISSUED:
        conditions.append(Receipt.voided_at.is_(None))
    elif receipt_status == ReceiptStatus.VOIDED:
        conditions.append(Receipt.voided_at.is_not(None))
    if date_from is not None:
        conditions.append(
            Receipt.issued_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        conditions.append(
            Receipt.issued_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Receipt.receipt_number).like(search),
                func.lower(Student.first_name).like(search),
                func.lower(Student.last_name).like(search),
                func.lower(
                    Student.first_name + " " + Student.last_name
                ).like(search),
                func.lower(Student.enrollment_number).like(search),
                func.lower(
                    func.coalesce(PaymentTransaction.reference_number, "")
                ).like(search),
            )
        )
    return conditions


def list_receipts(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    billing_month: date | None = None,
    payment_method: PaymentMethod | None = None,
    student_id: uuid.UUID | None = None,
    receipt_status: ReceiptStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Receipt], int]:
    conditions = _conditions(
        library_id,
        pagination,
        billing_month=billing_month,
        payment_method=payment_method,
        student_id=student_id,
        receipt_status=receipt_status,
        date_from=date_from,
        date_to=date_to,
    )
    joined = (
        select(Receipt)
        .join(Receipt.transaction)
        .join(PaymentTransaction.fee_record)
        .join(FeeRecord.student)
        .where(*conditions)
    )
    total = db.scalar(
        select(func.count()).select_from(joined.with_only_columns(Receipt.id).subquery())
    ) or 0
    sort_column = SORT_COLUMNS.get(pagination.sort_by, Receipt.issued_at)
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    records = list(
        db.scalars(
            joined.options(
                joinedload(Receipt.transaction).joinedload(
                    PaymentTransaction.recorded_by
                ),
                joinedload(Receipt.transaction)
                .joinedload(PaymentTransaction.fee_record)
                .joinedload(FeeRecord.student),
            )
            .order_by(ordering, Receipt.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        ).unique()
    )
    return records, total


def get_tenant_receipt(
    db: Session,
    library_id: uuid.UUID,
    receipt_id: uuid.UUID,
) -> Receipt | None:
    return db.scalar(
        select(Receipt)
        .join(Receipt.transaction)
        .join(PaymentTransaction.fee_record)
        .join(FeeRecord.student)
        .options(
            joinedload(Receipt.transaction).joinedload(
                PaymentTransaction.recorded_by
            ),
            joinedload(Receipt.transaction)
            .joinedload(PaymentTransaction.fee_record)
            .joinedload(FeeRecord.student),
        )
        .where(
            Receipt.id == receipt_id,
            Receipt.library_id == library_id,
            PaymentTransaction.library_id == library_id,
            PaymentTransaction.status == PaymentTransactionStatus.COMPLETED,
            FeeRecord.library_id == library_id,
            Student.library_id == library_id,
        )
    )
