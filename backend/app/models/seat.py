from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AllocationStatus,
    SeatOperationalStatus,
    SeatRequestStatus,
    SeatType,
    enum_type,
)


class Floor(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "floors"
    __table_args__ = (
        UniqueConstraint("library_id", "code", name="uq_floor_library_code"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    level_number: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    library: Mapped[object] = relationship("Library")
    seats: Mapped[list[Seat]] = relationship(back_populates="floor")


class Shift(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "shifts"
    __table_args__ = (
        UniqueConstraint("library_id", "name", name="uq_shift_library_name"),
        CheckConstraint("start_time <> end_time", name="start_and_end_differ"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    crosses_midnight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    library: Mapped[object] = relationship("Library")
    allocations: Mapped[list[SeatAllocation]] = relationship(back_populates="shift")


class Seat(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("library_id", "seat_number", name="uq_seat_library_number"),
        Index("ix_seat_library_floor_status", "library_id", "floor_id", "operational_status"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("floors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seat_number: Mapped[str] = mapped_column(String(64), nullable=False)
    seat_type: Mapped[SeatType] = mapped_column(
        enum_type(SeatType, "seat_type"),
        nullable=False,
        default=SeatType.STANDARD,
    )
    operational_status: Mapped[SeatOperationalStatus] = mapped_column(
        enum_type(SeatOperationalStatus, "seat_operational_status"),
        nullable=False,
        default=SeatOperationalStatus.AVAILABLE,
        index=True,
    )
    status_note: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    library: Mapped[object] = relationship("Library")
    floor: Mapped[Floor] = relationship(back_populates="seats")
    allocations: Mapped[list[SeatAllocation]] = relationship(back_populates="seat")
    status_events: Mapped[list[SeatStatusEvent]] = relationship(
        back_populates="seat",
        cascade="all, delete-orphan",
        order_by="SeatStatusEvent.effective_from",
    )


class SeatStatusEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seat_status_events"
    __table_args__ = (
        CheckConstraint(
            "effective_until IS NULL OR effective_until > effective_from",
            name="status_period_valid",
        ),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[SeatOperationalStatus | None] = mapped_column(
        enum_type(SeatOperationalStatus, "seat_previous_operational_status")
    )
    to_status: Mapped[SeatOperationalStatus] = mapped_column(
        enum_type(SeatOperationalStatus, "seat_new_operational_status"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    seat: Mapped[Seat] = relationship(back_populates="status_events")


class SeatAllocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seat_allocations"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="allocation_date_range_valid"),
        CheckConstraint("shift_start_time <> shift_end_time", name="allocation_shift_times_differ"),
        Index(
            "ix_allocation_seat_conflict_lookup",
            "library_id",
            "seat_id",
            "status",
            "start_date",
            "end_date",
        ),
        Index(
            "ix_allocation_student_conflict_lookup",
            "library_id",
            "student_id",
            "status",
            "start_date",
            "end_date",
        ),
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
    seat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AllocationStatus] = mapped_column(
        enum_type(AllocationStatus, "allocation_status"),
        nullable=False,
        default=AllocationStatus.ACTIVE,
        index=True,
    )
    shift_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    shift_end_time: Mapped[time] = mapped_column(Time, nullable=False)
    shift_crosses_midnight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    seat_number_snapshot: Mapped[str | None] = mapped_column(String(64))
    floor_id_snapshot: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True)
    )
    floor_name_snapshot: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    close_reason: Mapped[str | None] = mapped_column(Text)
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    allocated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    previous_allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("seat_allocations.id", ondelete="SET NULL")
    )
    transfer_group_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)

    library: Mapped[object] = relationship("Library")
    student: Mapped[object] = relationship("Student", back_populates="allocations")
    seat: Mapped[Seat] = relationship(back_populates="allocations")
    shift: Mapped[Shift] = relationship(back_populates="allocations")
    allocated_by: Mapped[object | None] = relationship(
        "User",
        foreign_keys=[allocated_by_user_id],
    )
    closed_by: Mapped[object | None] = relationship(
        "User",
        foreign_keys=[closed_by_user_id],
    )
    previous_allocation: Mapped[SeatAllocation | None] = relationship(
        remote_side="SeatAllocation.id",
        foreign_keys=[previous_allocation_id],
    )


class SeatChangeRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seat_change_requests"
    __table_args__ = (
        UniqueConstraint("library_id", "request_number", name="uq_seat_request_library_number"),
        CheckConstraint(
            "status <> 'rejected' OR admin_note IS NOT NULL",
            name="rejected_request_has_note",
        ),
        Index(
            "uq_pending_seat_request_per_student",
            "library_id",
            "student_id",
            unique=True,
            sqlite_where=text("status = 'pending'"),
            postgresql_where=text("status = 'pending'"),
        ),
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
    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    current_allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("seat_allocations.id", ondelete="SET NULL")
    )
    preferred_seat_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("seats.id", ondelete="SET NULL")
    )
    preferred_floor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("floors.id", ondelete="SET NULL")
    )
    preferred_shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SeatRequestStatus] = mapped_column(
        enum_type(SeatRequestStatus, "seat_request_status"),
        nullable=False,
        default=SeatRequestStatus.PENDING,
        index=True,
    )
    admin_note: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resulting_allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("seat_allocations.id", ondelete="SET NULL")
    )

    library: Mapped[object] = relationship("Library")
    student: Mapped[object] = relationship("Student", back_populates="seat_change_requests")
    current_allocation: Mapped[SeatAllocation | None] = relationship(
        foreign_keys=[current_allocation_id]
    )
    resulting_allocation: Mapped[SeatAllocation | None] = relationship(
        foreign_keys=[resulting_allocation_id]
    )
    preferred_seat: Mapped[Seat | None] = relationship(foreign_keys=[preferred_seat_id])
    preferred_floor: Mapped[Floor | None] = relationship(foreign_keys=[preferred_floor_id])
    preferred_shift: Mapped[Shift] = relationship(foreign_keys=[preferred_shift_id])
