"""PostgreSQL evidence for serializing seat-request reviews."""
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
from app.core.exceptions import ApplicationError
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.enums import (
    AllocationStatus,
    LibraryStatus,
    SeatOperationalStatus,
    SeatRequestStatus,
    SeatType,
    StudentStatus,
)
from app.models.identity import User
from app.models.library import Library
from app.models.seat import (
    Floor,
    Seat,
    SeatAllocation,
    SeatChangeRequest,
    Shift,
)
from app.models.student import Student
from app.schemas.seat_request import SeatRequestReview
from app.services.seat_request import review_request


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
        suffix = uuid.uuid4().hex[:8]
        library = Library(
            code=f"REQ-{suffix}",
            name="Seat Request Lock Test Library",
            contact_email=f"seat-request-lock-{suffix}@example.com",
            status=LibraryStatus.ACTIVE,
        )
        actor = User(
            email=f"seat-request-owner-{suffix}@example.com",
            password_hash="not-used",
            full_name="Seat Request Lock Owner",
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
        shift = Shift(
            library_id=library.id,
            name="Morning",
            start_time=time(6, 0),
            end_time=time(12, 0),
        )
        student = Student(
            library_id=library.id,
            enrollment_number=f"STU-{suffix}",
            first_name="Concurrent",
            last_name="Student",
            email=f"concurrent-student-{suffix}@example.com",
            phone="9876543210",
            joined_on=date.today(),
            monthly_fee=Decimal("1000.00"),
            status=StudentStatus.ACTIVE,
        )
        db.add_all([floor, shift, student])
        db.flush()
        seat = Seat(
            library_id=library.id,
            floor_id=floor.id,
            seat_number=f"A-{suffix[:4]}",
            seat_type=SeatType.STANDARD,
            operational_status=SeatOperationalStatus.AVAILABLE,
        )
        db.add(seat)
        db.flush()
        allocation = SeatAllocation(
            library_id=library.id,
            student_id=student.id,
            seat_id=seat.id,
            shift_id=shift.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=AllocationStatus.ACTIVE,
            shift_name=shift.name,
            shift_start_time=shift.start_time,
            shift_end_time=shift.end_time,
            shift_crosses_midnight=False,
            seat_number_snapshot=seat.seat_number,
            floor_id_snapshot=floor.id,
            floor_name_snapshot=floor.name,
            allocated_by_user_id=actor.id,
        )
        db.add(allocation)
        db.flush()
        request = SeatChangeRequest(
            library_id=library.id,
            student_id=student.id,
            request_number=f"SCR-{suffix}",
            current_allocation_id=allocation.id,
            preferred_floor_id=floor.id,
            preferred_shift_id=shift.id,
            reason="I need a quieter seat for examination preparation.",
            status=SeatRequestStatus.PENDING,
        )
        db.add(request)
        db.commit()
        return (
            library.id,
            actor.id,
            request.id,
            allocation.id,
            allocation.seat_id,
            allocation.shift_id,
        )


def _run_race(decisions: tuple[str, str]) -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"seat_request_lock_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(
        url,
        pool_size=5,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    sessions = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        Base.metadata.create_all(engine)
        (
            library_id,
            actor_id,
            request_id,
            allocation_id,
            seat_id,
            shift_id,
        ) = _seed(sessions)
        barrier = Barrier(2)

        def review_worker(decision: str) -> str:
            with sessions() as db:
                barrier.wait(timeout=10)
                try:
                    review_request(
                        db,
                        library_id,
                        request_id,
                        SeatRequestReview(
                            decision=decision,
                            review_note=(
                                "Requested seat is unavailable."
                                if decision == "rejected"
                                else None
                            ),
                        ),
                        actor_id,
                    )
                    return decision
                except ApplicationError:
                    db.rollback()
                    return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(review_worker, decision)
                for decision in decisions
            ]
            results = [future.result() for future in futures]
        assert results.count("conflict") == 1
        assert len(set(results) - {"conflict"}) == 1

        with sessions() as db:
            request = db.get(SeatChangeRequest, request_id)
            allocation = db.get(SeatAllocation, allocation_id)
            assert request is not None
            assert request.status.value in set(decisions)
            assert request.reviewed_by_user_id == actor_id
            assert request.resolved_at is not None
            assert request.resulting_allocation_id is None
            assert allocation is not None
            assert allocation.seat_id == seat_id
            assert allocation.shift_id == shift_id
            assert allocation.status == AllocationStatus.ACTIVE
            assert db.scalar(select(func.count(SeatAllocation.id))) == 1
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.entity_id == str(request_id),
                    AuditLog.action.in_(
                        [
                            "seat_change_request.approved",
                            "seat_change_request.rejected",
                        ]
                    ),
                )
            ) == 1
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()


def test_postgres_serializes_competing_approval_and_rejection() -> None:
    _run_race(("approved", "rejected"))


def test_postgres_serializes_duplicate_approvals() -> None:
    _run_race(("approved", "approved"))
