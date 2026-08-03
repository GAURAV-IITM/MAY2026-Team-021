"""Focused receipt and WhatsApp reminder rule tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest

from app.core.exceptions import BusinessRuleError
from app.services.reminder import (
    build_reminder_message,
    build_whatsapp_url,
    normalize_whatsapp_phone,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("+91 99999 99999", "919999999999"),
        ("+91-99999-99999", "919999999999"),
        ("+91 (99999) 99999", "919999999999"),
        ("919999999999", "919999999999"),
        ("99999 99999", "919999999999"),
        ("09999999999", "919999999999"),
    ],
)
def test_phone_normalization(source: str, expected: str) -> None:
    assert normalize_whatsapp_phone(source) == expected


@pytest.mark.parametrize(
    "source",
    [None, "", "123456789", "+91 abc", "++919999999999", "+123"],
)
def test_phone_normalization_rejects_unsafe_values(source: str | None) -> None:
    with pytest.raises(BusinessRuleError):
        normalize_whatsapp_phone(source)


def test_reminder_url_is_encoded_and_uses_current_balance() -> None:
    message = build_reminder_message(
        student_name="Aarav Sharma",
        library_name="Central Study Library",
        billing_month=date(2026, 7, 1),
        outstanding_balance=Decimal("600.00"),
        due_date=date(2026, 7, 10),
        library_phone=None,
    )
    url = build_whatsapp_url("919999999999", message)
    assert url.startswith("https://wa.me/919999999999?text=")
    decoded = parse_qs(urlsplit(url).query)["text"][0]
    assert "Aarav Sharma" in decoded
    assert "July 2026" in decoded
    assert "INR 600.00" in decoded
    assert "delivered" not in decoded.lower()
