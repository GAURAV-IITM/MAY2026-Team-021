from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AnnouncementAudience,
    AnnouncementPriority,
    AnnouncementStatus,
    enum_type,
)


class Announcement(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR scheduled_for IS NULL OR expires_at > scheduled_for",
            name="announcement_schedule_valid",
        ),
        Index("ix_announcement_library_status_publish", "library_id", "status", "published_at"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    priority: Mapped[AnnouncementPriority] = mapped_column(
        enum_type(AnnouncementPriority, "announcement_priority"),
        nullable=False,
        default=AnnouncementPriority.NORMAL,
    )
    audience: Mapped[AnnouncementAudience] = mapped_column(
        enum_type(AnnouncementAudience, "announcement_audience"),
        nullable=False,
        default=AnnouncementAudience.ALL_STUDENTS,
    )
    status: Mapped[AnnouncementStatus] = mapped_column(
        enum_type(AnnouncementStatus, "announcement_status"),
        nullable=False,
        default=AnnouncementStatus.DRAFT,
        index=True,
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    library: Mapped[object] = relationship("Library")
    author: Mapped[object | None] = relationship("User")
    reads: Mapped[list[AnnouncementRead]] = relationship(
        back_populates="announcement",
        cascade="all, delete-orphan",
    )


class AnnouncementRead(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "announcement_reads"
    __table_args__ = (
        UniqueConstraint("announcement_id", "student_id", name="uq_announcement_read_student"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    announcement: Mapped[Announcement] = relationship(back_populates="reads")
    student: Mapped[object] = relationship("Student")
