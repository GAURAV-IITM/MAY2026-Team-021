"""Tenant-scoped library settings queries."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.library import Library, LibrarySettings


def get_library_with_settings(
    db: Session,
    library_id: uuid.UUID,
) -> Library | None:
    return db.scalar(
        select(Library)
        .options(selectinload(Library.settings))
        .where(
            Library.id == library_id,
            Library.deleted_at.is_(None),
        )
    )


def get_settings(
    db: Session,
    library_id: uuid.UUID,
) -> LibrarySettings | None:
    return db.scalar(
        select(LibrarySettings).where(
            LibrarySettings.library_id == library_id,
        )
    )
