from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    DeliveryStatus,
    FeeStatus,
    PaymentMethod,
    PaymentTransactionStatus,
    ReminderChannel,
    enum_type,
)


class FeeRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fee_records"
    __table_args__ = (
        UniqueConstraint(
            "library_id",
            "student_id",
            "billing_month",
            name="uq_fee_record_student_month",
        ),
        CheckConstraint("base_amount >= 0", name="fee_base_amount_non_negative"),
        CheckConstraint("discount_amount >= 0", name="fee_discount_non_negative"),
        CheckConstraint("late_fee_amount >= 0", name="fee_late_amount_non_negative"),
        CheckConstraint("total_amount >= 0", name="fee_total_amount_non_negative"),
        Index("ix_fee_record_library_month_status", "library_id", "billing_month", "status"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    billing_month: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    late_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[FeeStatus] = mapped_column(
        enum_type(FeeStatus, "fee_status"),
        nullable=False,
        default=FeeStatus.UNPAID,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    generated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    waived_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    waived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    library: Mapped[object] = relationship("Library")
    student: Mapped[object] = relationship("Student")
    transactions: Mapped[list[PaymentTransaction]] = relationship(
        back_populates="fee_record",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[list[PaymentReminder]] = relationship(
        back_populates="fee_record",
        cascade="all, delete-orphan",
    )


class PaymentTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="payment_amount_positive"),
        Index("ix_payment_library_paid_at", "library_id", "paid_at"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fee_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fee_records.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        enum_type(PaymentMethod, "payment_method"),
        nullable=False,
    )
    status: Mapped[PaymentTransactionStatus] = mapped_column(
        enum_type(PaymentTransactionStatus, "payment_transaction_status"),
        nullable=False,
        default=PaymentTransactionStatus.COMPLETED,
        index=True,
    )
    reference_number: Mapped[str | None] = mapped_column(String(120), index=True)
    external_transaction_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    fee_record: Mapped[FeeRecord] = relationship(back_populates="transactions")
    recorded_by: Mapped[object | None] = relationship(
        "User",
        foreign_keys=[recorded_by_user_id],
    )
    receipt: Mapped[Receipt | None] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Receipt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("library_id", "receipt_number", name="uq_receipt_library_number"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_transactions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    receipt_number: Mapped[str] = mapped_column(String(80), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    void_reason: Mapped[str | None] = mapped_column(Text)
    voided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    transaction: Mapped[PaymentTransaction] = relationship(back_populates="receipt")


class PaymentReminder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_reminders"

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fee_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fee_records.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    channel: Mapped[ReminderChannel] = mapped_column(
        enum_type(ReminderChannel, "reminder_channel"),
        nullable=False,
    )
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        enum_type(DeliveryStatus, "reminder_delivery_status"),
        nullable=False,
        default=DeliveryStatus.QUEUED,
        index=True,
    )
    message_snapshot: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    fee_record: Mapped[FeeRecord] = relationship(back_populates="reminders")
