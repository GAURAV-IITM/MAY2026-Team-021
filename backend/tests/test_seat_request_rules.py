"""Seat-change request review schema rules."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.seat_request import SeatRequestReview


def test_approval_note_is_optional_and_trimmed() -> None:
    assert SeatRequestReview(decision="approved").review_note is None
    assert (
        SeatRequestReview(
            decision="approved",
            reviewNote="  Contact the front desk.  ",
        ).review_note
        == "Contact the front desk."
    )


@pytest.mark.parametrize("note", [None, "", "   ", "no"])
def test_rejection_requires_meaningful_note(note) -> None:
    with pytest.raises(ValidationError):
        SeatRequestReview(decision="rejected", reviewNote=note)


def test_invalid_decision_and_overlong_note_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SeatRequestReview(decision="pending")
    with pytest.raises(ValidationError):
        SeatRequestReview(decision="approved", reviewNote="x" * 2001)
