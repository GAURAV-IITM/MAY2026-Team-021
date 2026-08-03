"""PostgreSQL evidence that allocation row locks prevent double booking."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all model metadata
from app.core.exceptions import ConflictError
from app.db.base import Base
from app.models.enums import (
    LibraryStatus,
    SeatOperationalStatus,
    SeatType,
    StudentStatus,
)
from app.models.identity import User
from app.models.library import Library
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student
from app.schemas.allocation import SeatAllocationCreate
from app.services.allocation import create_allocations


POSTGRES_URL = os.getenv("TEST_POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Set TEST_POSTGRES_DATABASE_URL to run PostgreSQL lock tests.",
)


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _seed(session_factory):
    with session_factory() as db:
        library = Library(
            code=f"LOCK-{uuid.uuid4().hex[:8]}",
            name="Allocation Lock Test Library",
            contact_email=f"lock-{uuid.uuid4().hex[:8]}@example.com",
            status=LibraryStatus.ACTIVE,
        )
        actor = User(
            email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="not-used-by-this-test",
            full_name="Lock Test Owner",
        )
        db.add_all([library, actor])
        db.flush()
        library.primary_owner_user_id = actor.id
        floor = Floor(
            library_id=library.id,
            name="Ground Floor",
            code="GF",
            level_number=0,
        )
        db.add(floor)
        db.flush()
        seats = [
            Seat(
                library_id=library.id,
                floor_id=floor.id,
                seat_number=f"A-{index:02d}",
                seat_type=SeatType.STANDARD,
                operational_status=SeatOperationalStatus.AVAILABLE,
            )
            for index in range(1, 4)
        ]
        students = [
            Student(
                library_id=library.id,
                enrollment_number=f"LOCK-STU-{index}",
                first_name="Student",
                last_name=str(index),
                email=f"lock-student-{index}-{uuid.uuid4().hex[:6]}@example.com",
                phone=f"90000000{index:02d}",
                joined_on=date.today(),
                monthly_fee=Decimal("1000.00"),
                status=StudentStatus.ACTIVE,
            )
            for index in range(1, 4)
        ]
        shift = Shift(
            library_id=library.id,
            name="Office Hours",
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )
        db.add_all([*seats, *students, shift])
        db.commit()
        return (
            library.id,
            actor.id,
            [seat.id for seat in seats],
            [student.id for student in students],
            shift.id,
        )


def _race(
    session_factory,
    *,
    library_id,
    actor_id,
    attempts,
    shift_id,
):
    barrier = Barrier(len(attempts))

    def worker(student_id, seat_id):
        with session_factory() as db:
            barrier.wait(timeout=10)
            try:
                create_allocations(
                    db,
                    library_id,
                    SeatAllocationCreate(
                        student_id=student_id,
                        seat_id=seat_id,
                        shift_ids=[shift_id],
                        start_date=date.today(),
                        end_date=date.today() + timedelta(days=30),
                    ),
                    actor_id,
                )
                return "created"
            except ConflictError:
                db.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=len(attempts)) as executor:
        return list(executor.map(lambda values: worker(*values), attempts))


def test_postgres_locks_prevent_seat_and_student_double_booking() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"allocation_lock_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(
        url,
        pool_size=5,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        Base.metadata.create_all(engine)
        library_id, actor_id, seats, students, shift_id = _seed(
            session_factory
        )

        same_seat_results = _race(
            session_factory,
            library_id=library_id,
            actor_id=actor_id,
            attempts=[
                (students[0], seats[0]),
                (students[1], seats[0]),
            ],
            shift_id=shift_id,
        )
        assert sorted(same_seat_results) == ["conflict", "created"]

        same_student_results = _race(
            session_factory,
            library_id=library_id,
            actor_id=actor_id,
            attempts=[
                (students[2], seats[1]),
                (students[2], seats[2]),
            ],
            shift_id=shift_id,
        )
        assert sorted(same_student_results) == ["conflict", "created"]

        with session_factory() as db:
            count = db.scalar(
                select(func.count(SeatAllocation.id)).where(
                    SeatAllocation.library_id == library_id
                )
            )
            assert count == 2
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()
