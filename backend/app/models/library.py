from __future__ import annotations

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LibraryStatus, MembershipStatus, RoleName, enum_type


class Library(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "libraries"

    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    status: Mapped[LibraryStatus] = mapped_column(
        enum_type(LibraryStatus, "library_status"),
        nullable=False,
        default=LibraryStatus.PENDING,
        index=True,
    )
    primary_owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    suspension_reason: Mapped[str | None] = mapped_column(Text)

    primary_owner: Mapped[object | None] = relationship(
        "User",
        foreign_keys=[primary_owner_user_id],
    )
    settings: Mapped[LibrarySettings | None] = relationship(
        back_populates="library",
        cascade="all, delete-orphan",
        uselist=False,
    )
    memberships: Mapped[list[LibraryMembership]] = relationship(
        back_populates="library",
        cascade="all, delete-orphan",
    )


class LibraryMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "library_memberships"
    __table_args__ = (
        UniqueConstraint("library_id", "user_id", name="uq_membership_library_user"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[RoleName] = mapped_column(
        enum_type(RoleName, "membership_role"),
        nullable=False,
    )
    status: Mapped[MembershipStatus] = mapped_column(
        enum_type(MembershipStatus, "membership_status"),
        nullable=False,
        default=MembershipStatus.INVITED,
        index=True,
    )
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    library: Mapped[Library] = relationship(back_populates="memberships")
    user: Mapped[object] = relationship("User")


class LibrarySettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "library_settings"

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    opening_time: Mapped[time | None] = mapped_column(Time)
    closing_time: Mapped[time | None] = mapped_column(Time)
    weekly_off_days: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    default_monthly_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    fee_due_day: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    payment_grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    receipt_prefix: Mapped[str] = mapped_column(String(24), nullable=False, default="REC")
    allow_seat_change_requests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_seat_request_reason: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    whatsapp_reminders_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_pending_payments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_seat_requests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_maintenance_seats: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_announcement_copy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    library: Mapped[Library] = relationship(back_populates="settings")


class PlatformSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
