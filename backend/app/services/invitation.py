"""Shared secure account-invitation creation primitives."""
from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_token
from app.models.enums import InvitationStatus, RoleName
from app.models.identity import AccountInvitation


@dataclass(frozen=True, slots=True)
class CreatedAccountInvitation:
    invitation: AccountInvitation
    setup_url: str


def setup_url(raw_token: str) -> str:
    return (
        f"{settings.frontend_base_url}/accept-invitation?token="
        f"{quote(raw_token)}"
    )


def create_account_invitation(
    db: Session,
    *,
    library_id: uuid.UUID,
    email: str,
    role: RoleName,
    invited_by_user_id: uuid.UUID,
    invitee_name: str | None = None,
    invitee_phone: str | None = None,
) -> CreatedAccountInvitation:
    raw_token = secrets.token_urlsafe(48)
    invitation = AccountInvitation(
        library_id=library_id,
        email=email.strip().lower(),
        invitee_name=invitee_name,
        invitee_phone=invitee_phone,
        role=role,
        token_hash=hash_token(raw_token),
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.account_invitation_expire_hours),
        invited_by_user_id=invited_by_user_id,
    )
    db.add(invitation)
    db.flush()
    return CreatedAccountInvitation(
        invitation=invitation,
        setup_url=setup_url(raw_token),
    )
