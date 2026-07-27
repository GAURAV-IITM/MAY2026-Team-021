"""Pure allocation interval and status-precedence coverage."""
from datetime import date, time

import pytest

from app.services.allocation import date_ranges_overlap, time_ranges_overlap


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ((6, 0, 12, 0), (6, 0, 12, 0), True),
        ((6, 0, 12, 0), (9, 0, 17, 0), True),
        ((6, 0, 18, 0), (9, 0, 12, 0), True),
        ((6, 0, 12, 0), (12, 0, 18, 0), False),
        ((22, 0, 2, 0), (1, 0, 6, 0), True),
        ((22, 0, 2, 0), (6, 0, 12, 0), False),
    ],
)
def test_time_ranges_handle_boundaries_and_overnight_shifts(
    first,
    second,
    expected,
) -> None:
    assert time_ranges_overlap(
        time(first[0], first[1]),
        time(first[2], first[3]),
        time(second[0], second[1]),
        time(second[2], second[3]),
    ) is expected


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (("2026-08-01", "2026-08-10"), ("2026-08-01", "2026-08-10"), True),
        (("2026-08-01", "2026-08-10"), ("2026-08-05", "2026-08-15"), True),
        (("2026-08-01", "2026-08-20"), ("2026-08-05", "2026-08-10"), True),
        (("2026-08-01", "2026-08-10"), ("2026-08-11", "2026-08-20"), False),
    ],
)
def test_date_ranges_are_inclusive_and_allow_consecutive_periods(
    first,
    second,
    expected,
) -> None:
    assert date_ranges_overlap(
        date.fromisoformat(first[0]),
        date.fromisoformat(first[1]),
        date.fromisoformat(second[0]),
        date.fromisoformat(second[1]),
    ) is expected
