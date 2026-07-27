"""Library settings management use cases."""
from __future__ import annotations

import uuid
from datetime import time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.models.library import LibrarySettings
from app.repositories import library as repository
from app.schemas.library import LibrarySettingsResponse, LibrarySettingsUpdate


def _response(library, settings: LibrarySettings) -> LibrarySettingsResponse:
    weekly_off_days = settings.weekly_off_days or []
    return LibrarySettingsResponse(
        library_id=library.id,
        library_name=library.name,
        contact_email=library.contact_email,
        contact_phone=library.contact_phone,
        address=library.address_line,
        city=library.city,
        state=library.state,
        postal_code=library.postal_code,
        timezone=library.timezone,
        opening_time=settings.opening_time or time(6, 0),
        closing_time=settings.closing_time or time(23, 0),
        weekly_off=weekly_off_days[0] if weekly_off_days else "none",
        default_monthly_fee=float(settings.default_monthly_fee),
        fee_due_day=settings.fee_due_day,
        payment_grace_days=settings.payment_grace_days,
        receipt_prefix=settings.receipt_prefix,
        allow_seat_change_requests=settings.allow_seat_change_requests,
        require_seat_request_reason=settings.require_seat_request_reason,
        whatsapp_reminders_enabled=settings.whatsapp_reminders_enabled,
        notify_pending_payments=settings.notify_pending_payments,
        notify_seat_requests=settings.notify_seat_requests,
        notify_maintenance_seats=settings.notify_maintenance_seats,
        email_announcement_copy=settings.email_announcement_copy,
        updated_at=max(library.updated_at, settings.updated_at),
    )


def get_settings(
    db: Session,
    library_id: uuid.UUID,
) -> LibrarySettingsResponse:
    library = repository.get_library_with_settings(db, library_id)
    if library is None:
        raise ResourceNotFoundError("Library not found.", code="LIBRARY_NOT_FOUND")
    settings = library.settings
    if settings is None:
        settings = LibrarySettings(library_id=library.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return _response(library, settings)


def update_settings(
    db: Session,
    library_id: uuid.UUID,
    payload: LibrarySettingsUpdate,
) -> LibrarySettingsResponse:
    library = repository.get_library_with_settings(db, library_id)
    if library is None:
        raise ResourceNotFoundError("Library not found.", code="LIBRARY_NOT_FOUND")
    settings = library.settings
    if settings is None:
        settings = LibrarySettings(library_id=library.id)
        db.add(settings)

    library.name = payload.library_name.strip()
    library.contact_email = payload.contact_email.strip().lower()
    library.contact_phone = payload.contact_phone
    library.address_line = payload.address
    library.city = payload.city
    library.state = payload.state
    library.postal_code = payload.postal_code
    library.timezone = payload.timezone

    settings.opening_time = payload.opening_time
    settings.closing_time = payload.closing_time
    settings.weekly_off_days = (
        [] if payload.weekly_off == "none" else [payload.weekly_off.lower()]
    )
    settings.default_monthly_fee = Decimal(str(payload.default_monthly_fee))
    settings.fee_due_day = payload.fee_due_day
    settings.payment_grace_days = payload.payment_grace_days
    settings.receipt_prefix = payload.receipt_prefix.upper()
    settings.allow_seat_change_requests = payload.allow_seat_change_requests
    settings.require_seat_request_reason = payload.require_seat_request_reason
    settings.whatsapp_reminders_enabled = payload.whatsapp_reminders_enabled
    settings.notify_pending_payments = payload.notify_pending_payments
    settings.notify_seat_requests = payload.notify_seat_requests
    settings.notify_maintenance_seats = payload.notify_maintenance_seats
    settings.email_announcement_copy = payload.email_announcement_copy
    db.commit()
    db.refresh(library)
    db.refresh(settings)
    return _response(library, settings)
