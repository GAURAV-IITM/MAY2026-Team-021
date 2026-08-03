"""Focused announcement content, date, and timezone rules."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.core.exceptions import BusinessRuleError
from app.models.enums import AnnouncementStatus
from app.schemas.announcement import AnnouncementCreate
from app.services.announcement import _utc, _validate_dates


def _payload(**overrides):
    payload = {
        "title": "Valid announcement title",
        "body": "This is valid announcement body content.",
        "category": "general",
        "priority": "normal",
        "audience": "all_students",
        "status": "draft",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "    "),
        ("title", "abcd"),
        ("title", "x" * 121),
        ("body", "    "),
        ("body", "short"),
        ("body", "x" * 1001),
        ("category", "unsupported"),
        ("priority", "urgent"),
        ("audience", "another_library"),
    ],
)
def test_content_and_enum_validation_reject_invalid_values(
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValidationError):
        AnnouncementCreate(**_payload(**{field: value}))


def test_valid_content_and_supported_enums_are_accepted() -> None:
    payload = AnnouncementCreate(
        **_payload(
            category="fees",
            priority="important",
            audience="pending_fee_students",
        )
    )
    assert payload.title == "Valid announcement title"
    assert payload.category.value == "fees"


def test_schedule_expiry_and_timezone_rules() -> None:
    now = datetime.now(timezone.utc)
    scheduled = now + timedelta(hours=2)
    expires = scheduled + timedelta(hours=1)
    _validate_dates(
        AnnouncementStatus.SCHEDULED,
        scheduled,
        expires,
        now=now,
    )

    with pytest.raises(BusinessRuleError) as missing:
        _validate_dates(
            AnnouncementStatus.SCHEDULED,
            None,
            None,
            now=now,
        )
    assert missing.value.code == "ANNOUNCEMENT_SCHEDULE_REQUIRED"

    with pytest.raises(BusinessRuleError) as past:
        _validate_dates(
            AnnouncementStatus.SCHEDULED,
            now - timedelta(seconds=1),
            None,
            now=now,
        )
    assert past.value.code == "ANNOUNCEMENT_SCHEDULE_NOT_FUTURE"

    for invalid_expiry in (scheduled, scheduled - timedelta(seconds=1)):
        with pytest.raises(BusinessRuleError) as invalid:
            _validate_dates(
                AnnouncementStatus.SCHEDULED,
                scheduled,
                invalid_expiry,
                now=now,
            )
        assert invalid.value.code == "ANNOUNCEMENT_EXPIRY_BEFORE_PUBLISH"

    indian_time = datetime(
        2026,
        8,
        1,
        14,
        30,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    assert _utc(indian_time) == datetime(
        2026,
        8,
        1,
        9,
        0,
        tzinfo=timezone.utc,
    )
