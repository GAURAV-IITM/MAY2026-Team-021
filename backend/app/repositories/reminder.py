"""Tenant-scoped payment-reminder persistence."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.payment import PaymentReminder


def add(db: Session, reminder: PaymentReminder) -> PaymentReminder:
    db.add(reminder)
    db.flush()
    return reminder
