from __future__ import annotations

import unittest
from datetime import date, time
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.db.base import Base
from app.models import Floor, Library, Seat, SeatAllocation, Shift, Student, User
from app.models.enums import AllocationStatus


class DatabaseModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

        owner = User(
            email="owner@example.com",
            password_hash="not-a-real-password-hash",
            full_name="Library Owner",
        )
        library = Library(
            code="LIB-001",
            name="Central Study Library",
            contact_email="library@example.com",
            primary_owner=owner,
        )
        floor = Floor(library=library, name="Floor 1", code="F1", level_number=1)
        seat = Seat(library=library, floor=floor, seat_number="A-01")
        shift = Shift(
            library=library,
            name="Morning",
            start_time=time(6, 0),
            end_time=time(12, 0),
        )
        student = Student(
            library=library,
            enrollment_number="STU-001",
            first_name="Test",
            last_name="Student",
            email="student@example.com",
            phone="9999999999",
            monthly_fee=Decimal("1000.00"),
        )
        self.session.add_all([owner, library, floor, seat, shift, student])
        self.session.commit()

        self.library = library
        self.floor = floor
        self.seat = seat
        self.shift = shift
        self.student = student

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_all_models_register_and_configure(self) -> None:
        configure_mappers()
        self.assertEqual(24, len(Base.metadata.tables))

    def test_seat_number_is_unique_within_library(self) -> None:
        self.session.add(
            Seat(
                library=self.library,
                floor=self.floor,
                seat_number=self.seat.seat_number,
            )
        )

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()

    def test_allocation_end_date_cannot_precede_start_date(self) -> None:
        self.session.add(
            SeatAllocation(
                library_id=self.library.id,
                student=self.student,
                seat=self.seat,
                shift=self.shift,
                start_date=date(2026, 8, 31),
                end_date=date(2026, 8, 1),
                status=AllocationStatus.ACTIVE,
                shift_name=self.shift.name,
                shift_start_time=self.shift.start_time,
                shift_end_time=self.shift.end_time,
            )
        )

        with self.assertRaises(IntegrityError):
            self.session.commit()

        self.session.rollback()


if __name__ == "__main__":
    unittest.main()
