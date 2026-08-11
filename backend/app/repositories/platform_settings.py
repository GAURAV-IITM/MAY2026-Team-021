"""Persistence helpers for whitelisted platform settings."""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.library import PlatformSetting


def get_rows(
    db: Session,
    keys: Iterable[str],
    *,
    for_update: bool = False,
) -> dict[str, PlatformSetting]:
    requested = sorted(set(keys))
    if not requested:
        return {}
    query = (
        select(PlatformSetting)
        .where(PlatformSetting.key.in_(requested))
        .order_by(PlatformSetting.key.asc())
    )
    if for_update:
        query = query.with_for_update(of=PlatformSetting)
    return {row.key: row for row in db.scalars(query)}


def add_row(db: Session, row: PlatformSetting) -> PlatformSetting:
    db.add(row)
    db.flush()
    return row
