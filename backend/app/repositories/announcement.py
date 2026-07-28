"""Tenant-scoped announcement persistence."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.announcement import Announcement
from app.models.enums import (
    AnnouncementAudience,
    AnnouncementCategory,
    AnnouncementPriority,
    AnnouncementStatus,
)
from app.schemas.announcement import AnnouncementSummary
from app.schemas.common import PaginationParams


SORT_COLUMNS = {
    "createdAt": Announcement.created_at,
    "updatedAt": Announcement.updated_at,
    "title": Announcement.title,
    "status": Announcement.status,
    "category": Announcement.category,
    "priority": Announcement.priority,
    "scheduledAt": Announcement.scheduled_for,
    "publishedAt": Announcement.published_at,
}


def _conditions(
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    status: AnnouncementStatus | None,
    category: AnnouncementCategory | None,
    priority: AnnouncementPriority | None,
    audience: AnnouncementAudience | None,
    now: datetime,
) -> list[object]:
    conditions: list[object] = [
        Announcement.library_id == library_id,
        Announcement.deleted_at.is_(None),
    ]
    if status is not None:
        if status == AnnouncementStatus.EXPIRED:
            conditions.append(
                or_(
                    Announcement.status == AnnouncementStatus.EXPIRED,
                    (
                        (Announcement.status == AnnouncementStatus.PUBLISHED)
                        & Announcement.expires_at.is_not(None)
                        & (Announcement.expires_at <= now)
                    ),
                )
            )
        elif status == AnnouncementStatus.PUBLISHED:
            conditions.extend(
                [
                    Announcement.status == AnnouncementStatus.PUBLISHED,
                    or_(
                        Announcement.expires_at.is_(None),
                        Announcement.expires_at > now,
                    ),
                ]
            )
        else:
            conditions.append(Announcement.status == status)
    if category is not None:
        conditions.append(Announcement.category == category.value)
    if priority is not None:
        conditions.append(Announcement.priority == priority)
    if audience is not None:
        conditions.append(Announcement.audience == audience)
    if pagination.search:
        search = f"%{pagination.search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Announcement.title).like(search),
                func.lower(Announcement.body).like(search),
                func.lower(Announcement.category).like(search),
            )
        )
    return conditions


def list_announcements(
    db: Session,
    library_id: uuid.UUID,
    pagination: PaginationParams,
    *,
    status: AnnouncementStatus | None = None,
    category: AnnouncementCategory | None = None,
    priority: AnnouncementPriority | None = None,
    audience: AnnouncementAudience | None = None,
    now: datetime,
) -> tuple[list[Announcement], int, AnnouncementSummary]:
    conditions = _conditions(
        library_id,
        pagination,
        status=status,
        category=category,
        priority=priority,
        audience=audience,
        now=now,
    )
    total = db.scalar(
        select(func.count(Announcement.id)).where(*conditions)
    ) or 0

    sort_column = SORT_COLUMNS.get(
        pagination.sort_by,
        Announcement.created_at,
    )
    ordering = (
        sort_column.asc()
        if pagination.sort_order == "asc"
        else sort_column.desc()
    )
    announcements = list(
        db.scalars(
            select(Announcement)
            .options(selectinload(Announcement.author))
            .where(*conditions)
            .order_by(ordering, Announcement.id.asc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
    )

    # Summary cards describe the whole library, not only the filtered page.
    summary_conditions = [
        Announcement.library_id == library_id,
        Announcement.deleted_at.is_(None),
    ]
    counts = db.execute(
        select(
            func.count(Announcement.id),
            func.sum(
                case(
                    (Announcement.status == AnnouncementStatus.DRAFT, 1),
                    else_=0,
                )
            ),
            func.sum(
                case(
                    (
                        Announcement.status
                        == AnnouncementStatus.SCHEDULED,
                        1,
                    ),
                    else_=0,
                )
            ),
            func.sum(
                case(
                    (
                        (
                            Announcement.status
                            == AnnouncementStatus.PUBLISHED
                        )
                        & or_(
                            Announcement.expires_at.is_(None),
                            Announcement.expires_at > now,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            func.sum(
                case(
                    (
                        Announcement.status
                        == AnnouncementStatus.ARCHIVED,
                        1,
                    ),
                    else_=0,
                )
            ),
            func.sum(
                case(
                    (
                        or_(
                            Announcement.status
                            == AnnouncementStatus.EXPIRED,
                            (
                                (Announcement.status == AnnouncementStatus.PUBLISHED)
                                & Announcement.expires_at.is_not(None)
                                & (Announcement.expires_at <= now)
                            ),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            func.sum(
                case(
                    (
                        (Announcement.priority == AnnouncementPriority.IMPORTANT)
                        & (Announcement.status == AnnouncementStatus.PUBLISHED)
                        & or_(
                            Announcement.expires_at.is_(None),
                            Announcement.expires_at > now,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
        ).where(*summary_conditions)
    ).one()
    summary = AnnouncementSummary(
        total=counts[0] or 0,
        drafts=counts[1] or 0,
        scheduled=counts[2] or 0,
        published=counts[3] or 0,
        archived=counts[4] or 0,
        expired=counts[5] or 0,
        important=counts[6] or 0,
    )
    return announcements, total, summary


def get_announcement(
    db: Session,
    library_id: uuid.UUID,
    announcement_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> Announcement | None:
    query = (
        select(Announcement)
        .options(selectinload(Announcement.author))
        .where(
            Announcement.id == announcement_id,
            Announcement.library_id == library_id,
            Announcement.deleted_at.is_(None),
        )
    )
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def add_announcement(
    db: Session,
    announcement: Announcement,
) -> Announcement:
    db.add(announcement)
    db.flush()
    return announcement
