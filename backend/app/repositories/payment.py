"""Tenant-scoped monthly fee and payment transaction persistence."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    FeeStatus,
    PaymentTransactionStatus,
)
from app.models.library import Library, LibrarySettings
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.student import Student
from app.schemas.common import PaginationParams
from app.schemas.payment import PaymentSummary


SORT_COLUMNS = {
    "createdAt": FeeRecord.created_at,
    "updatedAt": FeeRecord.updated_at,
    "month": FeeRecord.billing_month,
    "billingMonth": FeeRecord.billing_month,
    "dueDate": FeeRecord.due_date,
    "totalAmount": FeeRecord.total_amount,
    "status": FeeRecord.status,
    "studentName": Student.first_name,
}


def lock_library(db: Session, library_id: uuid.UUID) -> Library | None:
    return db.scalar(
        select(Library)
        .where(
            Library.id == library_id,
            Library.deleted_at.is_(None),
        )
        .with_for_update()
    )


def get_library_settings(
    db: Session,
    library_id: uuid.UUID,
) -> LibrarySettings | None:
    return db.scalar(
        select(LibrarySettings).where(
            LibrarySettings.library_id == library_id,
        )
    )


def list_students_for_generation(
    db: Session,
    library_id: uuid.UUID,
) -> list[Student]:
    return list(
        db.scalars(
            select(Student)
            .where(
                Student.library_id == library_id,
                Student.deleted_at.is_(None),
            )
            .order_by(Student.first_name.asc(), Student.last_name.asc())
        )
    )


def existing_student_ids_for_month(
    db: Session,
    library_id: uuid.UUID,
    billing_month: date,
) -> set[uuid.UUID]:
    return set(
        db.scalars(
            select(FeeRecord.student_id).where(
                FeeRecord.library_id == library_id,
                FeeRecord.billing_month == billing_month,
            )
        )
    )


def _payment_conditions(
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    billing_month: date | None,
    status: FeeStatus | None,
    student_id: uuid.UUID | None,
    due_date_from: date | None,
    due_date_to: date | None,
    has_transactions: bool | None,
) -> list[object]:
    conditions: list[object] = [FeeRecord.library_id == library_id]
    if billing_month is not None:
        conditions.append(FeeRecord.billing_month == billing_month)
    if status is not None:
        conditions.append(FeeRecord.status == status)
    if student_id is not None:
        conditions.append(FeeRecord.student_id == student_id)
    if due_date_from is not None:
        conditions.append(FeeRecord.due_date >= due_date_from)
    if due_date_to is not None:
        conditions.append(FeeRecord.due_date <= due_date_to)
    if has_transactions is not None:
        transaction_exists = (
            select(PaymentTransaction.id)
            .where(
                PaymentTransaction.fee_record_id == FeeRecord.id,
                PaymentTransaction.library_id == library_id,
                PaymentTransaction.status
                == PaymentTransactionStatus.COMPLETED,
            )
            .exists()
        )
        conditions.append(
            transaction_exists if has_transactions else ~transaction_exists
        )
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Student.first_name).like(search),
                func.lower(Student.last_name).like(search),
                func.lower(
                    Student.first_name + " " + Student.last_name
                ).like(search),
                func.lower(Student.email).like(search),
                func.lower(Student.enrollment_number).like(search),
                func.lower(Student.phone).like(search),
            )
        )
    return conditions


def list_fee_records(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    billing_month: date | None = None,
    status: FeeStatus | None = None,
    student_id: uuid.UUID | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    has_transactions: bool | None = None,
) -> tuple[list[FeeRecord], int, PaymentSummary]:
    conditions = _payment_conditions(
        library_id,
        pagination,
        billing_month=billing_month,
        status=status,
        student_id=student_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        has_transactions=has_transactions,
    )
    base_query = select(FeeRecord.id).join(Student).where(*conditions)
    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    paid_subquery = (
        select(
            PaymentTransaction.fee_record_id.label("fee_record_id"),
            func.sum(PaymentTransaction.amount).label("paid_amount"),
        )
        .where(
            PaymentTransaction.status
            == PaymentTransactionStatus.COMPLETED
        )
        .group_by(PaymentTransaction.fee_record_id)
        .subquery()
    )
    paid_amount = func.coalesce(
        paid_subquery.c.paid_amount,
        Decimal("0.00"),
    )
    aggregate = db.execute(
        select(
            func.count(FeeRecord.id),
            func.coalesce(func.sum(FeeRecord.total_amount), 0),
            func.coalesce(func.sum(paid_amount), 0),
            func.coalesce(
                func.sum(FeeRecord.total_amount - paid_amount),
                0,
            ),
            func.sum(
                case((FeeRecord.status == FeeStatus.UNPAID, 1), else_=0)
            ),
            func.sum(
                case(
                    (FeeRecord.status == FeeStatus.PARTIALLY_PAID, 1),
                    else_=0,
                )
            ),
            func.sum(
                case((FeeRecord.status == FeeStatus.PAID, 1), else_=0)
            ),
        )
        .join(Student)
        .outerjoin(
            paid_subquery,
            paid_subquery.c.fee_record_id == FeeRecord.id,
        )
        .where(*conditions)
    ).one()
    summary = PaymentSummary(
        total_records=aggregate[0] or 0,
        total_billed_amount=aggregate[1] or Decimal("0.00"),
        total_collected_amount=aggregate[2] or Decimal("0.00"),
        total_pending_amount=aggregate[3] or Decimal("0.00"),
        unpaid_count=aggregate[4] or 0,
        partially_paid_count=aggregate[5] or 0,
        paid_count=aggregate[6] or 0,
    )

    sort_column = SORT_COLUMNS.get(
        pagination.sort_by,
        FeeRecord.created_at,
    )
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    records = list(
        db.scalars(
            select(FeeRecord)
            .join(Student)
            .options(
                selectinload(FeeRecord.student),
                selectinload(FeeRecord.transactions).selectinload(
                    PaymentTransaction.recorded_by
                ),
            )
            .where(*conditions)
            .order_by(ordering, FeeRecord.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        ).unique()
    )
    return records, total, summary


def get_fee_record_for_update(
    db: Session,
    library_id: uuid.UUID,
    fee_record_id: uuid.UUID,
) -> FeeRecord | None:
    return db.scalar(
        select(FeeRecord)
        .options(
            selectinload(FeeRecord.student),
            selectinload(FeeRecord.transactions).selectinload(
                PaymentTransaction.recorded_by
            ),
        )
        .where(
            FeeRecord.id == fee_record_id,
            FeeRecord.library_id == library_id,
        )
        .with_for_update()
    )


def reference_exists(
    db: Session,
    library_id: uuid.UUID,
    fee_record_id: uuid.UUID,
    reference_number: str,
) -> bool:
    return (
        db.scalar(
            select(func.count(PaymentTransaction.id)).where(
                PaymentTransaction.library_id == library_id,
                PaymentTransaction.fee_record_id == fee_record_id,
                func.lower(PaymentTransaction.reference_number)
                == reference_number.lower(),
                PaymentTransaction.status
                == PaymentTransactionStatus.COMPLETED,
            )
        )
        or 0
    ) > 0
