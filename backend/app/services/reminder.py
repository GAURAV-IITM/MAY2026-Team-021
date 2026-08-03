"""Auditable WhatsApp payment-reminder link generation."""
from __future__ import annotations

import re
import uuid
from datetime import date
from decimal import Decimal
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError
from app.models.enums import DeliveryStatus, FeeStatus, ReminderChannel
from app.models.identity import User
from app.models.payment import PaymentReminder
from app.repositories import payment as payment_repository
from app.repositories import reminder as repository
from app.schemas.receipt import (
    ReceiptActorSummary,
    ReminderAttemptResponse,
    ReminderCreateRequest,
    ReminderOutcome,
    WhatsAppReminderResponse,
)
from app.services.audit import AuditContext, write_audit_log
from app.services.payment import completed_paid_amount, money


ZERO = Decimal("0.00")
PHONE_CHARACTERS = re.compile(r"^[+\d\s()\-]+$")
DEFAULT_COUNTRY_CODE = "91"


def normalize_whatsapp_phone(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        raise BusinessRuleError(
            "The student does not have a phone number.",
            code="REMINDER_PHONE_MISSING",
        )
    if not PHONE_CHARACTERS.fullmatch(raw):
        raise BusinessRuleError(
            "The student phone number contains unsupported characters.",
            code="REMINDER_PHONE_INVALID",
        )
    if raw.count("+") > 1 or ("+" in raw and not raw.startswith("+")):
        raise BusinessRuleError(
            "The student phone number is not in a valid international format.",
            code="REMINDER_PHONE_INVALID",
        )
    had_international_prefix = raw.startswith("+")
    digits = re.sub(r"[\s()\-]", "", raw)
    if digits.startswith("+"):
        digits = digits[1:]
    if not digits.isdigit():
        raise BusinessRuleError(
            "The student phone number must contain digits only after "
            "formatting characters are removed.",
            code="REMINDER_PHONE_INVALID",
        )
    if not had_international_prefix and len(digits) == 10:
        digits = f"{DEFAULT_COUNTRY_CODE}{digits}"
    elif (
        not had_international_prefix
        and len(digits) == 11
        and digits.startswith("0")
    ):
        digits = f"{DEFAULT_COUNTRY_CODE}{digits[1:]}"
    if not 8 <= len(digits) <= 15:
        raise BusinessRuleError(
            "The student phone number must contain 8 to 15 digits including "
            "the country code.",
            code="REMINDER_PHONE_INVALID",
        )
    if not had_international_prefix and len(digits) < 11:
        raise BusinessRuleError(
            "The student phone number is too short to generate a WhatsApp link.",
            code="REMINDER_COUNTRY_CODE_REQUIRED",
        )
    return digits


def mask_phone(phone: str) -> str:
    visible = phone[-4:]
    return f"{'*' * max(len(phone) - 4, 0)}{visible}"


def build_reminder_message(
    *,
    student_name: str,
    library_name: str,
    billing_month: date,
    outstanding_balance: Decimal,
    due_date: date,
    library_phone: str | None,
) -> str:
    month_label = billing_month.strftime("%B %Y")
    due_line = (
        f"This payment was due on {due_date.strftime('%d %B %Y')}."
        if due_date < date.today()
        else f"Due date: {due_date.strftime('%d %B %Y')}."
    )
    contact_line = (
        f" Contact the library at {library_phone} if you need assistance."
        if library_phone
        else " Please contact the library if you need assistance."
    )
    return (
        f"Hello {student_name},\n\n"
        f"This is a reminder from {library_name} that your library fee for "
        f"{month_label} has an outstanding balance of "
        f"INR {money(outstanding_balance):.2f}.\n\n"
        f"{due_line}{contact_line}\n\n"
        "If you have already paid, please contact the library so the record "
        "can be checked."
    )


def build_whatsapp_url(phone: str, message: str) -> str:
    return f"https://wa.me/{phone}?text={quote(message, safe='')}"


def create_whatsapp_reminder(
    db: Session,
    library_id: uuid.UUID,
    fee_record_id: uuid.UUID,
    payload: ReminderCreateRequest,
    actor_user_id: uuid.UUID,
    *,
    audit_context: AuditContext | None = None,
) -> WhatsAppReminderResponse:
    try:
        fee = payment_repository.get_fee_record_for_update(
            db,
            library_id,
            fee_record_id,
        )
        if fee is None or fee.student.deleted_at is not None:
            raise ResourceNotFoundError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        paid_amount = completed_paid_amount(fee)
        outstanding = max(money(fee.total_amount) - paid_amount, ZERO)
        if fee.status in {FeeStatus.PAID, FeeStatus.WAIVED, FeeStatus.CANCELLED}:
            raise ConflictError(
                "A reminder cannot be created for a closed payment record.",
                code="REMINDER_PAYMENT_CLOSED",
            )
        if outstanding <= ZERO:
            raise ConflictError(
                "This fee has no outstanding balance.",
                code="REMINDER_PAYMENT_ALREADY_PAID",
            )
        settings = payment_repository.get_library_settings(db, library_id)
        if settings is None or not settings.whatsapp_reminders_enabled:
            raise ConflictError(
                "WhatsApp payment reminders are disabled in library settings.",
                code="WHATSAPP_REMINDERS_DISABLED",
            )
        library = payment_repository.lock_library(db, library_id)
        if library is None:
            raise ResourceNotFoundError(
                "Library not found.",
                code="LIBRARY_NOT_FOUND",
            )

        phone = normalize_whatsapp_phone(fee.student.phone)
        student_name = (
            f"{fee.student.first_name} {fee.student.last_name}".strip()
        )
        message = payload.message or build_reminder_message(
            student_name=student_name,
            library_name=library.name,
            billing_month=fee.billing_month,
            outstanding_balance=outstanding,
            due_date=fee.due_date,
            library_phone=library.contact_phone,
        )
        whatsapp_url = build_whatsapp_url(phone, message)
        actor = db.get(User, actor_user_id)
        reminder = repository.add(
            db,
            PaymentReminder(
                library_id=library_id,
                student_id=fee.student_id,
                fee_record_id=fee.id,
                channel=ReminderChannel.WHATSAPP,
                recipient=phone,
                status=DeliveryStatus.QUEUED,
                message_snapshot=message,
                sent_at=None,
                error_message=None,
                sent_by_user_id=actor_user_id,
            ),
        )
        write_audit_log(
            db,
            library_id=library_id,
            actor_user_id=actor_user_id,
            action="payment_reminder.link_generated",
            entity_type="payment_reminder",
            entity_id=str(reminder.id),
            new_values={
                "feeRecordId": str(fee.id),
                "studentId": str(fee.student_id),
                "channel": ReminderChannel.WHATSAPP.value,
                "outcome": ReminderOutcome.LINK_GENERATED.value,
                "outstandingBalance": str(money(outstanding)),
                "maskedPhone": mask_phone(phone),
            },
            request_context=audit_context,
        )
        db.commit()
        return WhatsAppReminderResponse(
            reminder=ReminderAttemptResponse(
                id=reminder.id,
                fee_record_id=fee.id,
                student_id=fee.student_id,
                channel=ReminderChannel.WHATSAPP,
                outcome=ReminderOutcome.LINK_GENERATED,
                attempted_at=reminder.created_at,
                initiated_by=(
                    ReceiptActorSummary(id=actor.id, name=actor.full_name)
                    if actor
                    else None
                ),
                masked_phone=mask_phone(phone),
                message=message,
            ),
            whatsapp_url=whatsapp_url,
        )
    except Exception:
        db.rollback()
        raise
