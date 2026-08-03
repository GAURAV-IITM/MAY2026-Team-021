"""Pure calculation coverage for Owner dashboard and report rules."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import BusinessRuleError
from app.services.report import (
    _normalize_month_range,
    ageing_bucket,
    money,
    month_range,
    percentage,
)


@pytest.mark.parametrize(
    ("part", "total", "expected"),
    [
        (0, 0, 0.0),
        (0, 10, 0.0),
        (1, 3, 33.33),
        (2, 3, 66.67),
        (10, 10, 100.0),
    ],
)
def test_percentage_handles_zero_and_rounds(
    part: int,
    total: int,
    expected: float,
) -> None:
    assert percentage(part, total) == expected


def test_money_uses_decimal_precision() -> None:
    assert money(Decimal("0.10") + Decimal("0.20")) == Decimal("0.30")


@pytest.mark.parametrize(
    ("days_overdue", "expected_key"),
    [
        (-1, "not_due"),
        (0, "not_due"),
        (1, "1_30"),
        (30, "1_30"),
        (31, "31_60"),
        (60, "31_60"),
        (61, "61_90"),
        (90, "61_90"),
        (91, "90_plus"),
    ],
)
def test_ageing_bucket_boundaries(
    days_overdue: int,
    expected_key: str,
) -> None:
    assert ageing_bucket(days_overdue)[0] == expected_key


def test_month_range_is_inclusive() -> None:
    assert month_range(date(2026, 1, 1), date(2026, 3, 1)) == [
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


@pytest.mark.parametrize(
    ("start_month", "end_month"),
    [
        ("2026-13", "2026-12"),
        ("July 2026", "2026-08"),
        ("2026-08", "2026-07"),
        ("2024-01", "2026-02"),
    ],
)
def test_invalid_month_ranges_are_rejected(
    start_month: str,
    end_month: str,
) -> None:
    with pytest.raises(BusinessRuleError) as raised:
        _normalize_month_range(
            "Asia/Kolkata",
            start_month=start_month,
            end_month=end_month,
        )

    assert raised.value.code == "REPORT_INVALID_MONTH_RANGE"
