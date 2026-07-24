from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import StudentStatus, enum_type


class Student(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("library_id", "enrollment_number", name="uq_student_library_enrollment"),
        UniqueConstraint("library_id", "email", name="uq_student_library_email"),
        CheckConstraint("monthly_fee >= 0", name="monthly_fee_non_negative"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        index=True,
    )
    enrollment_number: Mapped[str] = mapped_column(String(64), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    guardian_name: Mapped[str | None] = mapped_column(String(160))
    guardian_phone: Mapped[str | None] = mapped_column(String(32))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    preferred_language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    joined_on: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    left_on: Mapped[date | None] = mapped_column(Date)
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[StudentStatus] = mapped_column(
        enum_type(StudentStatus, "student_status"),
        nullable=False,
        default=StudentStatus.ACTIVE,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    library: Mapped[object] = relationship("Library")
    user: Mapped[object | None] = relationship("User")
    allocations: Mapped[list[object]] = relationship(
        "SeatAllocation",
        back_populates="student",
    )
    seat_change_requests: Mapped[list[object]] = relationship(
        "SeatChangeRequest",
        back_populates="student",
    )
