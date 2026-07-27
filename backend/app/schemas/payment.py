"""Monthly fee generation and payment transaction API contracts."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import FeeStatus, PaymentMethod, PaymentTransactionStatus
from app.schemas.common import APIModel, PaginationMeta
from app.schemas.receipt import ReceiptListItem


MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class PaymentStudentSummary(APIModel):
    id: uuid.UUID
    enrollment_number: str
    name: str
    email: str
    phone: str


class PaymentActorSummary(APIModel):
    id: uuid.UUID
    name: str


class PaymentTransactionCreate(APIModel):
    model_config = {
        **APIModel.model_config,
        "json_schema_extra": {
            "examples": [
                {
                    "amount": "500.00",
                    "method": "upi",
                    "paidAt": "2026-07-27T10:30:00+05:30",
                    "referenceNumber": "UPI-20260727-001",
                    "notes": "First instalment.",
                }
            ]
        },
    }

    amount: Decimal = Field(
        gt=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )
    method: PaymentMethod
    paid_at: datetime | None = None
    reference_number: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("reference_number", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        return cleaned or None


class PaymentTransactionResponse(APIModel):
    id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    status: PaymentTransactionStatus
    reference_number: str | None
    paid_at: datetime
    notes: str | None
    recorded_by: PaymentActorSummary | None
    created_at: datetime


class FeeRecordResponse(APIModel):
    id: uuid.UUID
    student: PaymentStudentSummary
    month: str = Field(pattern=MONTH_PATTERN)
    due_date: date
    base_amount: Decimal
    discount_amount: Decimal
    late_fee_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    status: FeeStatus
    notes: str | None
    latest_transaction: PaymentTransactionResponse | None
    transactions: list[PaymentTransactionResponse]
    created_at: datetime
    updated_at: datetime


class PaymentSummary(APIModel):
    total_records: int = Field(ge=0)
    unpaid_count: int = Field(ge=0)
    partially_paid_count: int = Field(ge=0)
    paid_count: int = Field(ge=0)
    total_billed_amount: Decimal = Field(ge=0)
    total_collected_amount: Decimal = Field(ge=0)
    total_pending_amount: Decimal = Field(ge=0)


class PaymentListResponse(APIModel):
    message: str
    data: list[FeeRecordResponse]
    meta: PaginationMeta
    summary: PaymentSummary


class MonthlyFeeGenerationRequest(APIModel):
    model_config = {
        **APIModel.model_config,
        "json_schema_extra": {
            "examples": [{"month": "2026-07"}],
        },
    }

    month: str = Field(pattern=MONTH_PATTERN)


class MonthlyFeeGenerationSkip(APIModel):
    student_id: uuid.UUID
    student_name: str
    reason: str
    message: str


class MonthlyFeeGenerationResponse(APIModel):
    month: str = Field(pattern=MONTH_PATTERN)
    active_student_count: int = Field(ge=0)
    eligible_student_count: int = Field(ge=0)
    created_count: int = Field(ge=0)
    existing_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    created_payments: list[FeeRecordResponse]
    skipped_students: list[MonthlyFeeGenerationSkip]


class PaymentTransactionRecordedResponse(APIModel):
    payment: FeeRecordResponse
    transaction: PaymentTransactionResponse
    receipt: ReceiptListItem
