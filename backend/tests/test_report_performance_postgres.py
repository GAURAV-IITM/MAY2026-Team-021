"""PostgreSQL report profiling with a realistic, isolated tenant dataset."""
from __future__ import annotations

import os
import time as clock
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all SQLAlchemy metadata
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.enums import (
    AllocationStatus,
    FeeStatus,
    LibraryStatus,
    PaymentMethod,
    PaymentTransactionStatus,
    SeatOperationalStatus,
    SeatType,
    StudentStatus,
)
from app.models.identity import User
from app.models.library import Library
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.seat import Floor, Seat, SeatAllocation, Shift
from app.models.student import Student
from app.services.report import get_dashboard, get_reports


POSTGRES_URL = os.getenv("TEST_POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Set TEST_POSTGRES_DATABASE_URL to run report profiling.",
)

STUDENT_COUNT = 500
SEAT_COUNT = 500
SHIFT_COUNT = 6
MONTH_COUNT = 6
AUDIT_COUNT = 1000


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _add_months(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _seed(session_factory):
    today = date.today()
    current_month = today.replace(day=1)
    with session_factory() as db:
        suffix = uuid.uuid4().hex[:8]
        library = Library(
            code=f"RPT-{suffix}",
            name="Report Performance Library",
            contact_email=f"report-performance-{suffix}@example.com",
            timezone="Asia/Kolkata",
            status=LibraryStatus.ACTIVE,
        )
        actor = User(
            email=f"report-performance-owner-{suffix}@example.com",
            password_hash="not-used",
            full_name="Report Performance Owner",
        )
        db.add_all([library, actor])
        db.flush()
        library.primary_owner_user_id = actor.id

        floors = [
            Floor(
                library_id=library.id,
                name=f"Floor {index + 1}",
                code=f"F{index + 1}",
                level_number=index + 1,
                sort_order=index + 1,
            )
            for index in range(5)
        ]
        shifts = [
            Shift(
                library_id=library.id,
                name=f"Shift {index + 1}",
                start_time=time((index * 4) % 24),
                end_time=time(((index + 1) * 4) % 24),
                crosses_midnight=index == SHIFT_COUNT - 1,
            )
            for index in range(SHIFT_COUNT)
        ]
        db.add_all([*floors, *shifts])
        db.flush()

        students = [
            Student(
                library_id=library.id,
                enrollment_number=f"RPT-{index + 1:05d}",
                first_name="Report",
                last_name=f"Student {index + 1}",
                email=f"report-student-{suffix}-{index + 1}@example.com",
                phone=f"9{index + 1:09d}",
                joined_on=_add_months(current_month, -(index % MONTH_COUNT)),
                monthly_fee=Decimal("1000.00"),
                status=(
                    StudentStatus.ACTIVE
                    if index % 10
                    else StudentStatus.INACTIVE
                ),
            )
            for index in range(STUDENT_COUNT)
        ]
        seats = [
            Seat(
                library_id=library.id,
                floor_id=floors[index % len(floors)].id,
                seat_number=f"S-{index + 1:04d}",
                seat_type=SeatType.STANDARD,
                operational_status=(
                    SeatOperationalStatus.MAINTENANCE
                    if index % 50 == 0
                    else SeatOperationalStatus.AVAILABLE
                ),
            )
            for index in range(SEAT_COUNT)
        ]
        db.add_all([*students, *seats])
        db.flush()

        allocations = []
        for index, student in enumerate(students):
            for offset in range(2):
                shift = shifts[(index + offset * 3) % len(shifts)]
                seat = seats[index % len(seats)]
                allocations.append(
                    SeatAllocation(
                        library_id=library.id,
                        student_id=student.id,
                        seat_id=seat.id,
                        shift_id=shift.id,
                        start_date=today - timedelta(days=30),
                        end_date=today + timedelta(days=30),
                        status=AllocationStatus.ACTIVE,
                        shift_name=shift.name,
                        shift_start_time=shift.start_time,
                        shift_end_time=shift.end_time,
                        shift_crosses_midnight=shift.crosses_midnight,
                        seat_number_snapshot=seat.seat_number,
                        floor_id_snapshot=seat.floor_id,
                        floor_name_snapshot=floors[index % len(floors)].name,
                        allocated_by_user_id=actor.id,
                    )
                )
        db.add_all(allocations)

        fees = []
        for month_offset in range(-(MONTH_COUNT - 1), 1):
            billing_month = _add_months(current_month, month_offset)
            for student in students:
                fees.append(
                    FeeRecord(
                        library_id=library.id,
                        student_id=student.id,
                        billing_month=billing_month,
                        due_date=billing_month + timedelta(days=9),
                        base_amount=Decimal("1000.00"),
                        total_amount=Decimal("1000.00"),
                        status=FeeStatus.UNPAID,
                        generated_by_user_id=actor.id,
                    )
                )
        db.add_all(fees)
        db.flush()

        transactions = []
        for index, fee in enumerate(fees):
            if index % 3 == 0:
                continue
            fee.status = FeeStatus.PARTIALLY_PAID
            transactions.append(
                PaymentTransaction(
                    library_id=library.id,
                    student_id=fee.student_id,
                    fee_record_id=fee.id,
                    amount=Decimal("500.00"),
                    method=PaymentMethod.UPI,
                    status=PaymentTransactionStatus.COMPLETED,
                    reference_number=f"RPT-{suffix}-{index}",
                    paid_at=datetime.now(timezone.utc),
                    recorded_by_user_id=actor.id,
                )
            )
        audits = [
            AuditLog(
                library_id=library.id,
                actor_user_id=actor.id,
                action="payment_transaction.recorded",
                entity_type="payment_transaction",
                entity_id=str(index),
                new_values={"amount": "500.00"},
                request_id=f"report-profile-{index}",
                created_at=datetime.now(timezone.utc),
            )
            for index in range(AUDIT_COUNT)
        ]
        db.add_all([*transactions, *audits])
        db.commit()
        return library.id, current_month


def test_postgres_report_query_count_plans_and_response_size() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"report_profile_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(
        url,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    sessions = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        Base.metadata.create_all(engine)
        library_id, current_month = _seed(sessions)
        query_count = 0

        def count_query(*_args) -> None:
            nonlocal query_count
            query_count += 1

        event.listen(engine, "before_cursor_execute", count_query)
        with sessions() as db:
            dashboard_start = clock.perf_counter()
            dashboard = get_dashboard(
                db,
                library_id,
                "Asia/Kolkata",
                report_date=date.today(),
                billing_month=current_month.strftime("%Y-%m"),
            )
            dashboard_seconds = clock.perf_counter() - dashboard_start
            dashboard_queries = query_count

            query_count = 0
            report_start = clock.perf_counter()
            reports = get_reports(
                db,
                library_id,
                "Asia/Kolkata",
                start_month=_add_months(
                    current_month,
                    -(MONTH_COUNT - 1),
                ).strftime("%Y-%m"),
                end_month=current_month.strftime("%Y-%m"),
            )
            report_seconds = clock.perf_counter() - report_start
            report_queries = query_count
        event.remove(engine, "before_cursor_execute", count_query)

        with engine.connect() as connection:
            plans = {
                "fees": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) "
                        "SELECT * FROM fee_records "
                        "WHERE library_id = :library_id "
                        "AND billing_month BETWEEN :start_month AND :end_month"
                    ),
                    {
                        "library_id": library_id,
                        "start_month": _add_months(
                            current_month,
                            -(MONTH_COUNT - 1),
                        ),
                        "end_month": current_month,
                    },
                ).scalars().all(),
                "allocations": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) "
                        "SELECT * FROM seat_allocations "
                        "WHERE library_id = :library_id "
                        "AND status = 'active' "
                        "AND start_date <= :report_date "
                        "AND end_date >= :report_date"
                    ),
                    {
                        "library_id": library_id,
                        "report_date": date.today(),
                    },
                ).scalars().all(),
                "audits": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) "
                        "SELECT * FROM audit_logs "
                        "WHERE library_id = :library_id "
                        "ORDER BY created_at DESC LIMIT 6"
                    ),
                    {"library_id": library_id},
                ).scalars().all(),
            }

        dashboard_bytes = len(dashboard.model_dump_json(by_alias=True))
        report_bytes = len(reports.model_dump_json(by_alias=True))
        print(
            {
                "dataset": {
                    "students": STUDENT_COUNT,
                    "seats": SEAT_COUNT,
                    "shifts": SHIFT_COUNT,
                    "allocations": STUDENT_COUNT * 2,
                    "fees": STUDENT_COUNT * MONTH_COUNT,
                    "transactions": STUDENT_COUNT * MONTH_COUNT * 2 // 3,
                    "audits": AUDIT_COUNT,
                },
                "dashboardSeconds": round(dashboard_seconds, 4),
                "dashboardQueries": dashboard_queries,
                "dashboardBytes": dashboard_bytes,
                "reportSeconds": round(report_seconds, 4),
                "reportQueries": report_queries,
                "reportBytes": report_bytes,
                "plans": plans,
            }
        )
        assert dashboard_queries <= 20
        assert report_queries <= 18
        assert len(dashboard.recent_activity) <= 6
        assert len(dashboard.students_requiring_attention) <= 6
        assert len(reports.pending_payments.records) <= 200
        assert all(plans.values())
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()
