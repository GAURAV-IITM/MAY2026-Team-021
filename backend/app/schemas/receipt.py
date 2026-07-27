"""Receipt and WhatsApp payment-reminder API contracts."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator

from app.models.enums import FeeStatus, PaymentMethod, ReminderChannel
from app.schemas.common import APIModel, PaginationMeta


MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class ReceiptStatus(StrEnum):
    ISSUED = "issued"
    VOIDED = "voided"


class ReminderOutcome(StrEnum):
    LINK_GENERATED = "link_generated"
    FAILED = "failed"


class ReceiptStudentSummary(APIModel):
    id: uuid.UUID
    name: str
    enrollment_number: str


class ReceiptLibrarySummary(APIModel):
    id: uuid.UUID
    name: str
    address: str | None
    phone: str | None
    email: str


class ReceiptActorSummary(APIModel):
    id: uuid.UUID
    name: str


class ReceiptFeeSummary(APIModel):
    id: uuid.UUID
    billing_month: str = Field(pattern=MONTH_PATTERN)
    due_date: date
    total_amount: Decimal
    previously_paid_amount: Decimal
    payment_amount: Decimal
    remaining_balance: Decimal
    payment_status: FeeStatus


class ReceiptPaymentSummary(APIModel):
    id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    reference_number: str | None
    paid_at: datetime
    recorded_by: ReceiptActorSummary | None
    notes: str | None


class ReceiptListItem(APIModel):
    id: uuid.UUID
    receipt_number: str
    student: ReceiptStudentSummary
    fee_record_id: uuid.UUID
    payment_transaction_id: uuid.UUID
    billing_month: str = Field(pattern=MONTH_PATTERN)
    amount: Decimal
    payment_method: PaymentMethod
    payment_reference: str | None
    paid_at: datetime
    issued_at: datetime
    status: ReceiptStatus
    currency: str = "INR"
    download_available: bool = True


class ReceiptListResponse(APIModel):
    message: str
    data: list[ReceiptListItem]
    meta: PaginationMeta


class ReceiptDetail(APIModel):
    id: uuid.UUID
    receipt_number: str
    status: ReceiptStatus
    issued_at: datetime
    currency: str = "INR"
    library: ReceiptLibrarySummary
    student: ReceiptStudentSummary
    fee: ReceiptFeeSummary
    payment: ReceiptPaymentSummary


class ReminderCreateRequest(APIModel):
    model_config = {
        **APIModel.model_config,
        "json_schema_extra": {
            "examples": [
                {
                    "channel": "whatsapp",
                    "message": None,
                }
            ]
        },
    }

    channel: Literal[ReminderChannel.WHATSAPP] = ReminderChannel.WHATSAPP
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        return cleaned or None


class ReminderAttemptResponse(APIModel):
    id: uuid.UUID
    fee_record_id: uuid.UUID
    student_id: uuid.UUID
    channel: ReminderChannel
    outcome: ReminderOutcome
    attempted_at: datetime
    initiated_by: ReceiptActorSummary | None
    masked_phone: str
    message: str


class WhatsAppReminderResponse(APIModel):
    reminder: ReminderAttemptResponse
    whatsapp_url: str
