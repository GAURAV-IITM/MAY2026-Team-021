"""Tenant-safe monthly billing and payment transaction use cases."""
from __future__ import annotations

import calendar
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ResourceNotFoundError,
)
from app.models.enums import (
    FeeStatus,
    PaymentTransactionStatus,
    StudentStatus,
)
from app.models.identity import User
from app.models.payment import FeeRecord, PaymentTransaction
from app.repositories import payment as repository
from app.schemas.common import PaginationParams
from app.schemas.payment import (
    FeeRecordResponse,
    MonthlyFeeGenerationRequest,
    MonthlyFeeGenerationResponse,
    MonthlyFeeGenerationSkip,
    PaymentActorSummary,
    PaymentStudentSummary,
    PaymentSummary,
    PaymentTransactionCreate,
    PaymentTransactionRecordedResponse,
    PaymentTransactionResponse,
)
from app.services.audit import AuditContext, write_audit_log


ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class PaymentListResult:
    payments: list[FeeRecordResponse]
    total: int
    summary: PaymentSummary


def _billing_month(value: str) -> date:
    year, month = (int(part) for part in value.split("-"))
    return date(year, month, 1)


def _month_end(month: date) -> date:
    return date(
        month.year,
        month.month,
        calendar.monthrange(month.year, month.month)[1],
    )


def _due_date(month: date, due_day: int) -> date:
    return date(
        month.year,
        month.month,
        min(due_day, calendar.monthrange(month.year, month.month)[1]),
    )


def _money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def _completed_paid_amount(fee: FeeRecord) -> Decimal:
    return _money(
        sum(
            (
                transaction.amount
                for transaction in fee.transactions
                if transaction.status
                == PaymentTransactionStatus.COMPLETED
            ),
            ZERO,
        )
    )


def _timestamp_value(value: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def _transaction_response(
    transaction: PaymentTransaction,
) -> PaymentTransactionResponse:
    actor = transaction.recorded_by
    return PaymentTransactionResponse(
        id=transaction.id,
        amount=transaction.amount,
        method=transaction.method,
        status=transaction.status,
        reference_number=transaction.reference_number,
        paid_at=transaction.paid_at,
        notes=transaction.notes,
        recorded_by=(
            PaymentActorSummary(id=actor.id, name=actor.full_name)
            if actor
            else None
        ),
        created_at=transaction.created_at,
    )


def _fee_response(fee: FeeRecord) -> FeeRecordResponse:
    paid_amount = _completed_paid_amount(fee)
    balance = max(_money(fee.total_amount) - paid_amount, ZERO)
    transactions = sorted(
        fee.transactions,
        key=lambda transaction: (
            _timestamp_value(transaction.paid_at),
            _timestamp_value(transaction.created_at),
        ),
        reverse=True,
    )
    transaction_responses = [
        _transaction_response(transaction)
        for transaction in transactions
    ]
    return FeeRecordResponse(
        id=fee.id,
        student=PaymentStudentSummary(
            id=fee.student.id,
            enrollment_number=fee.student.enrollment_number,
            name=f"{fee.student.first_name} {fee.student.last_name}".strip(),
            email=fee.student.email,
            phone=fee.student.phone,
        ),
        month=fee.billing_month.strftime("%Y-%m"),
        due_date=fee.due_date,
        base_amount=fee.base_amount,
        discount_amount=fee.discount_amount,
        late_fee_amount=fee.late_fee_amount,
        total_amount=fee.total_amount,
        paid_amount=paid_amount,
        balance_amount=balance,
        status=fee.status,
        notes=fee.notes,
        latest_transaction=(
            transaction_responses[0] if transaction_responses else None
        ),
        transactions=transaction_responses,
        created_at=fee.created_at,
        updated_at=fee.updated_at,
    )


def list_payments(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    month: str | None = None,
    status: FeeStatus | None = None,
    student_id: uuid.UUID | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    has_transactions: bool | None = None,
) -> PaymentListResult:
    if due_date_from and due_date_to and due_date_to < due_date_from:
        raise BusinessRuleError(
            "Due date end cannot be earlier than due date start.",
            code="PAYMENT_DUE_DATE_RANGE_INVALID",
        )
    records, total, summary = repository.list_fee_records(
        db,
        library_id,
        pagination,
        billing_month=_billing_month(month) if month else None,
        status=status,
        student_id=student_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        has_transactions=has_transactions,
    )
    return PaymentListResult(
        payments=[_fee_response(record) for record in records],
        total=total,
        summary=summary,
    )


def generate_monthly_fees(
    db: Session,
    library_id: uuid.UUID,
    payload: MonthlyFeeGenerationRequest,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> MonthlyFeeGenerationResponse:
    billing_month = _billing_month(payload.month)
    month_end = _month_end(billing_month)
    try:
        if repository.lock_library(db, library_id) is None:
            raise ResourceNotFoundError(
                "Library not found.",
                code="LIBRARY_NOT_FOUND",
            )
        settings = repository.get_library_settings(db, library_id)
        if settings is None:
            raise BusinessRuleError(
                "Library fee settings must be configured first.",
                code="LIBRARY_FEE_SETTINGS_REQUIRED",
            )

        students = repository.list_students_for_generation(db, library_id)
        active_students = [
            student
            for student in students
            if student.status == StudentStatus.ACTIVE
        ]
        existing_student_ids = repository.existing_student_ids_for_month(
            db,
            library_id,
            billing_month,
        )
        created: list[FeeRecord] = []
        skipped: list[MonthlyFeeGenerationSkip] = []
        existing_count = 0
        eligible_count = 0

        for student in students:
            student_name = (
                f"{student.first_name} {student.last_name}".strip()
            )
            if student.status != StudentStatus.ACTIVE:
                skipped.append(
                    MonthlyFeeGenerationSkip(
                        student_id=student.id,
                        student_name=student_name,
                        reason="student_not_active",
                        message=(
                            f"Student status is {student.status.value}; "
                            "only active students are billed."
                        ),
                    )
                )
                continue
            if (
                student.joined_on > month_end
                or (
                    student.left_on is not None
                    and student.left_on < billing_month
                )
            ):
                skipped.append(
                    MonthlyFeeGenerationSkip(
                        student_id=student.id,
                        student_name=student_name,
                        reason="outside_membership_period",
                        message=(
                            "Student was not enrolled during this billing month."
                        ),
                    )
                )
                continue

            eligible_count += 1
            if student.id in existing_student_ids:
                existing_count += 1
                continue

            configured_fee = _money(student.monthly_fee)
            if configured_fee <= ZERO:
                configured_fee = _money(settings.default_monthly_fee)
            if configured_fee <= ZERO:
                skipped.append(
                    MonthlyFeeGenerationSkip(
                        student_id=student.id,
                        student_name=student_name,
                        reason="fee_not_configured",
                        message=(
                            "Neither the student fee nor the library default "
                            "fee is greater than zero."
                        ),
                    )
                )
                continue

            record = FeeRecord(
                library_id=library_id,
                student_id=student.id,
                billing_month=billing_month,
                due_date=_due_date(
                    billing_month,
                    settings.fee_due_day,
                ),
                base_amount=configured_fee,
                discount_amount=ZERO,
                late_fee_amount=ZERO,
                total_amount=configured_fee,
                status=FeeStatus.UNPAID,
                generated_by_user_id=actor_user_id,
            )
            record.student = student
            db.add(record)
            created.append(record)

        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="monthly_fees.generated",
            entity_type="fee_record_batch",
            entity_id=payload.month,
            new_values={
                "month": payload.month,
                "createdCount": len(created),
                "existingCount": existing_count,
                "skippedCount": len(skipped),
            },
            request_context=audit_context,
        )
        db.commit()
        return MonthlyFeeGenerationResponse(
            month=payload.month,
            active_student_count=len(active_students),
            eligible_student_count=eligible_count,
            created_count=len(created),
            existing_count=existing_count,
            skipped_count=len(skipped),
            created_payments=[_fee_response(record) for record in created],
            skipped_students=skipped,
        )
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Monthly fee generation conflicted with another request. "
            "Refresh the payment list; existing records were preserved.",
            code="MONTHLY_FEE_GENERATION_CONFLICT",
        ) from exc
    except Exception:
        db.rollback()
        raise


def record_payment(
    db: Session,
    library_id: uuid.UUID,
    fee_record_id: uuid.UUID,
    payload: PaymentTransactionCreate,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> PaymentTransactionRecordedResponse:
    try:
        fee = repository.get_fee_record_for_update(
            db,
            library_id,
            fee_record_id,
        )
        if fee is None:
            raise ResourceNotFoundError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        if fee.status == FeeStatus.PAID:
            raise ConflictError(
                "This monthly fee is already fully paid.",
                code="PAYMENT_ALREADY_PAID",
            )
        if fee.status in {FeeStatus.WAIVED, FeeStatus.CANCELLED}:
            raise ConflictError(
                "Payments cannot be recorded for a waived or cancelled fee.",
                code="PAYMENT_RECORD_CLOSED",
            )

        paid_at = payload.paid_at or datetime.now(timezone.utc)
        if paid_at.tzinfo is None:
            paid_at = paid_at.replace(tzinfo=timezone.utc)
        if paid_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise BusinessRuleError(
                "Payment date cannot be in the future.",
                code="PAYMENT_DATE_IN_FUTURE",
            )
        if (
            payload.reference_number
            and repository.reference_exists(
                db,
                library_id,
                fee.id,
                payload.reference_number,
            )
        ):
            raise ConflictError(
                "A transaction with this reference already exists "
                "for the payment record.",
                code="PAYMENT_REFERENCE_EXISTS",
            )

        paid_before = _completed_paid_amount(fee)
        balance_before = _money(fee.total_amount) - paid_before
        status_before = fee.status
        amount = _money(payload.amount)
        if amount > balance_before:
            raise BusinessRuleError(
                "Payment amount cannot be greater than the remaining balance.",
                code="PAYMENT_AMOUNT_EXCEEDS_BALANCE",
                details={
                    "remainingBalance": str(balance_before),
                    "submittedAmount": str(amount),
                },
            )

        actor = db.get(User, actor_user_id)
        transaction = PaymentTransaction(
            library_id=library_id,
            student_id=fee.student_id,
            fee_record_id=fee.id,
            amount=amount,
            method=payload.method,
            status=PaymentTransactionStatus.COMPLETED,
            reference_number=payload.reference_number,
            paid_at=paid_at,
            recorded_by_user_id=actor_user_id,
            notes=payload.notes,
        )
        transaction.recorded_by = actor
        fee.transactions.append(transaction)
        paid_after = paid_before + amount
        fee.status = (
            FeeStatus.PAID
            if paid_after == _money(fee.total_amount)
            else FeeStatus.PARTIALLY_PAID
        )
        db.flush()
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="payment_transaction.recorded",
            entity_type="payment_transaction",
            entity_id=str(transaction.id),
            old_values={
                "feeRecordId": str(fee.id),
                "paidAmount": str(paid_before),
                "balanceAmount": str(balance_before),
                "feeStatus": status_before.value,
            },
            new_values={
                "feeRecordId": str(fee.id),
                "studentId": str(fee.student_id),
                "amount": str(amount),
                "method": payload.method.value,
                "referenceNumber": payload.reference_number,
                "paidAmount": str(paid_after),
                "balanceAmount": str(
                    _money(fee.total_amount) - paid_after
                ),
                "feeStatus": fee.status.value,
            },
            request_context=audit_context,
        )
        db.commit()
        return PaymentTransactionRecordedResponse(
            payment=_fee_response(fee),
            transaction=_transaction_response(transaction),
        )
    except Exception:
        db.rollback()
        raise
