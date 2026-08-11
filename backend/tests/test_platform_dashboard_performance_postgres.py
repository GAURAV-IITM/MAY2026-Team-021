"""PostgreSQL profiling for platform dashboard aggregates."""
from __future__ import annotations

import os
import time as clock
import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers SQLAlchemy metadata
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.enums import LibraryStatus, RoleName, StudentStatus
from app.models.identity import Role, User, UserRole
from app.models.library import Library
from app.models.seat import Floor, Seat
from app.models.student import Student
from app.services.platform import get_dashboard


POSTGRES_URL = os.getenv("TEST_POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Set TEST_POSTGRES_DATABASE_URL to run platform dashboard profiling.",
)

LIBRARY_COUNT = 50
OWNER_COUNT = 100
STUDENT_COUNT = 5000
SEAT_COUNT = 1000
AUDIT_COUNT = 2000


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _add_months(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _seed(session_factory) -> None:
    now = datetime.now(timezone.utc)
    current_month = date.today().replace(day=1)
    suffix = uuid.uuid4().hex[:8]
    with session_factory() as db:
        owner_role = Role(name=RoleName.LIBRARY_OWNER, description="Owner")
        db.add(owner_role)
        db.flush()
        libraries = [
            Library(
                code=f"PDB-{suffix}-{index:03d}",
                name=f"Platform Dashboard Library {index + 1}",
                contact_email=f"pdb-library-{suffix}-{index}@example.com",
                status=(
                    LibraryStatus.SUSPENDED
                    if index % 10 == 0
                    else LibraryStatus.PENDING
                    if index % 7 == 0
                    else LibraryStatus.ACTIVE
                ),
                created_at=now - timedelta(days=index * 8),
            )
            for index in range(LIBRARY_COUNT)
        ]
        owners = [
            User(
                email=f"pdb-owner-{suffix}-{index}@example.com",
                password_hash="not-used",
                full_name=f"Platform Owner {index + 1}",
                is_active=index % 12 != 0,
                role_links=[
                    UserRole(
                        role=owner_role,
                        assigned_at=now - timedelta(days=index * 3),
                    )
                ],
            )
            for index in range(OWNER_COUNT)
        ]
        db.add_all([*libraries, *owners])
        db.flush()

        floors = [
            Floor(
                library_id=library.id,
                name="Ground Floor",
                code="GF",
            )
            for library in libraries
        ]
        db.add_all(floors)
        db.flush()
        students = [
            Student(
                library_id=libraries[index % LIBRARY_COUNT].id,
                enrollment_number=f"PDB-{index:06d}",
                first_name="Platform",
                last_name=f"Student {index + 1}",
                email=f"pdb-student-{suffix}-{index}@example.com",
                phone=f"9{index:09d}",
                joined_on=_add_months(current_month, -(index % 18)),
                monthly_fee=1000,
                status=(
                    StudentStatus.INACTIVE
                    if index % 20 == 0
                    else StudentStatus.ACTIVE
                ),
            )
            for index in range(STUDENT_COUNT)
        ]
        seats = [
            Seat(
                library_id=libraries[index % LIBRARY_COUNT].id,
                floor_id=floors[index % LIBRARY_COUNT].id,
                seat_number=f"PDB-{index:05d}",
            )
            for index in range(SEAT_COUNT)
        ]
        audits = [
            AuditLog(
                library_id=libraries[index % LIBRARY_COUNT].id,
                actor_user_id=owners[index % OWNER_COUNT].id,
                action=(
                    "platform.library.activated"
                    if index % 2
                    else "platform.owner.assigned"
                ),
                entity_type="library" if index % 2 else "owner",
                entity_id=str(libraries[index % LIBRARY_COUNT].id),
                created_at=now - timedelta(minutes=index),
            )
            for index in range(AUDIT_COUNT)
        ]
        db.add_all([*students, *seats, *audits])
        db.commit()


def test_postgres_platform_dashboard_query_count_plans_and_response_size() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"platform_dashboard_profile_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        Base.metadata.create_all(engine)
        _seed(sessions)
        query_count = 0

        def count_query(*_args) -> None:
            nonlocal query_count
            query_count += 1

        event.listen(engine, "before_cursor_execute", count_query)
        start = clock.perf_counter()
        with sessions() as db:
            dashboard = get_dashboard(db)
        elapsed = clock.perf_counter() - start
        event.remove(engine, "before_cursor_execute", count_query)

        with engine.connect() as connection:
            plans = {
                "libraries": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) SELECT status, COUNT(*) "
                        "FROM libraries WHERE deleted_at IS NULL GROUP BY status"
                    )
                ).scalars().all(),
                "students": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) SELECT joined_on, COUNT(*) "
                        "FROM students WHERE deleted_at IS NULL GROUP BY joined_on"
                    )
                ).scalars().all(),
                "audits": connection.execute(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM audit_logs "
                        "WHERE action LIKE 'platform.%' ORDER BY created_at DESC LIMIT 6"
                    )
                ).scalars().all(),
            }

        response_bytes = len(dashboard.model_dump_json(by_alias=True))
        print(
            {
                "dataset": {
                    "libraries": LIBRARY_COUNT,
                    "owners": OWNER_COUNT,
                    "students": STUDENT_COUNT,
                    "seats": SEAT_COUNT,
                    "audits": AUDIT_COUNT,
                },
                "seconds": round(elapsed, 4),
                "queries": query_count,
                "responseBytes": response_bytes,
                "plans": plans,
            }
        )
        assert dashboard.totals.total_libraries == LIBRARY_COUNT
        assert dashboard.totals.total_owners == OWNER_COUNT
        assert dashboard.totals.total_students == STUDENT_COUNT
        assert query_count <= 12
        assert elapsed < 5
        assert response_bytes < 100_000
        assert all(plans.values())
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()
