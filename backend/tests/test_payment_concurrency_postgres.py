"""PostgreSQL evidence for monthly generation and payment row locks."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all model metadata
from app.core.exceptions import ApplicationError
from app.db.base import Base
from app.models.enums import LibraryStatus, StudentStatus
from app.models.identity import User
from app.models.library import Library, LibrarySettings
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.student import Student
from app.schemas.payment import (
    MonthlyFeeGenerationRequest,
    PaymentTransactionCreate,
)
from app.services.payment import generate_monthly_fees, record_payment


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
            code=f"PAY-{suffix}",
            name="Payment Lock Test Library",
            contact_email=f"payment-lock-{suffix}@example.com",
            status=LibraryStatus.ACTIVE,
        )
        actor = User(
            email=f"payment-owner-{suffix}@example.com",
            password_hash="not-used",
            full_name="Payment Lock Owner",
        )
        db.add_all([library, actor])
        db.flush()
        library.primary_owner_user_id = actor.id
        db.add(
            LibrarySettings(
                library_id=library.id,
                default_monthly_fee=Decimal("100.00"),
                fee_due_day=10,
            )
        )
        student = Student(
            library_id=library.id,
            enrollment_number=f"PAY-STU-{suffix}",
            first_name="Payment",
            last_name="Student",
            email=f"payment-student-{suffix}@example.com",
            phone="9000000001",
            joined_on=date(2026, 1, 1),
            monthly_fee=Decimal("100.00"),
            status=StudentStatus.ACTIVE,
        )
        db.add(student)
        db.commit()
        return library.id, actor.id


def test_postgres_locks_generation_and_payment_transactions() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"payment_lock_{uuid.uuid4().hex}"
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
        library_id, actor_id = _seed(session_factory)

        generation_barrier = Barrier(2)

        def generate_worker():
            with session_factory() as db:
                generation_barrier.wait(timeout=10)
                result = generate_monthly_fees(
                    db,
                    library_id,
                    MonthlyFeeGenerationRequest(month="2026-07"),
                    actor_id,
                )
                return result.created_count, result.existing_count

        with ThreadPoolExecutor(max_workers=2) as executor:
            generation_results = list(
                executor.map(lambda _: generate_worker(), range(2))
            )
        assert sorted(generation_results) == [(0, 1), (1, 0)]

        with session_factory() as db:
            fee_id = db.scalar(select(FeeRecord.id))

        def run_payment_race(target_fee_id, amount, references):
            payment_barrier = Barrier(2)

            def payment_worker(reference: str):
                with session_factory() as db:
                    payment_barrier.wait(timeout=10)
                    try:
                        record_payment(
                            db,
                            library_id,
                            target_fee_id,
                            PaymentTransactionCreate(
                                amount=amount,
                                method="cash",
                                reference_number=reference,
                            ),
                            actor_id,
                        )
                        return "recorded"
                    except ApplicationError:
                        db.rollback()
                        return "rejected"

            with ThreadPoolExecutor(max_workers=2) as executor:
                return list(executor.map(payment_worker, references))

        payment_results = run_payment_race(
            fee_id,
            Decimal("100.00"),
            ["LOCK-PAYMENT-1", "LOCK-PAYMENT-2"],
        )
        assert sorted(payment_results) == ["recorded", "rejected"]

        with session_factory() as db:
            august = generate_monthly_fees(
                db,
                library_id,
                MonthlyFeeGenerationRequest(month="2026-08"),
                actor_id,
            )
            partial_fee_id = august.created_payments[0].id
        partial_results = run_payment_race(
            partial_fee_id,
            Decimal("60.00"),
            ["LOCK-PARTIAL-1", "LOCK-PARTIAL-2"],
        )
        assert sorted(partial_results) == ["recorded", "rejected"]

        with session_factory() as db:
            assert db.scalar(
                select(func.count(FeeRecord.id))
            ) == 2
            assert db.scalar(
                select(func.count(PaymentTransaction.id))
            ) == 2
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()
