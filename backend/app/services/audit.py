"""Atomic audit-log writer used by administrative mutation services."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


@dataclass(frozen=True, slots=True)
class AuditContext:
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


def write_audit_log(
    db: Session,
    *,
    library_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    request_context: AuditContext | None = None,
) -> AuditLog:
    request_context = request_context or AuditContext()
    record = AuditLog(
        library_id=library_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        context=context,
        ip_address=request_context.ip_address,
        user_agent=request_context.user_agent,
        request_id=request_context.request_id,
    )
    db.add(record)
    db.flush()
    return record
