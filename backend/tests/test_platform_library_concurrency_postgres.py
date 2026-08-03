"""PostgreSQL evidence for platform-library transaction and row-lock rules."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all model metadata
from app.core.exceptions import ApplicationError
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.enums import LibraryStatus, RoleName
from app.models.identity import Role, User, UserRole
from app.models.library import Library, LibraryMembership
from app.schemas.platform import (
    PlatformLibraryCreate,
    PlatformLibraryOwnerAssign,
    PlatformLibraryStatusUpdate,
)
from app.services.platform import (
    assign_library_owner,
    change_library_status,
    create_library,
)


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


def _database():
    url = _normalize_url(POSTGRES_URL)
    schema = f"platform_library_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url,
        pool_size=6,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    return schema, admin_engine, engine, factory


def _cleanup(schema, admin_engine, engine) -> None:
    engine.dispose()
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    admin_engine.dispose()


def _seed_actor_and_owner(factory):
    with factory() as db:
        admin_role = Role(name=RoleName.SUPER_ADMIN, description="Platform administrator")
        owner_role = Role(name=RoleName.LIBRARY_OWNER, description="Library owner")
        actor = User(
            email=f"platform-admin-{uuid.uuid4().hex}@example.com",
            password_hash="not-used",
            full_name="Platform Admin",
        )
        owner = User(
            email=f"platform-owner-{uuid.uuid4().hex}@example.com",
            password_hash="not-used",
            full_name="Platform Owner",
        )
        actor.role_links.append(UserRole(role=admin_role))
        owner.role_links.append(UserRole(role=owner_role))
        db.add_all([actor, owner])
        db.commit()
        return actor.id, owner.id


def test_postgres_prevents_concurrent_duplicate_library_creation() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, _owner_id = _seed_actor_and_owner(factory)
        barrier = Barrier(2)

        def create_worker(index: int) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    create_library(
                        db,
                        PlatformLibraryCreate(
                            name="Concurrent Library",
                            code="CONCURRENT",
                            contactEmail=f"concurrent-{index}@example.com",
                        ),
                        actor_id,
                    )
                    return "created"
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create_worker, range(2)))
        assert sorted(results) == ["created", "rejected"]
        with factory() as db:
            assert db.scalar(
                select(func.count(Library.id)).where(Library.code == "CONCURRENT")
            ) == 1
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "platform.library.created"
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)


def test_postgres_serializes_concurrent_owner_assignment() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, owner_id = _seed_actor_and_owner(factory)
        with factory() as db:
            libraries = [
                Library(
                    code=f"OWNER-{index}",
                    name=f"Owner Assignment {index}",
                    contact_email=f"owner-assignment-{index}@example.com",
                    status=LibraryStatus.PENDING,
                )
                for index in range(2)
            ]
            db.add_all(libraries)
            db.commit()
            library_ids = [library.id for library in libraries]
        barrier = Barrier(2)

        def assign_worker(library_id: uuid.UUID) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    assign_library_owner(
                        db,
                        library_id,
                        PlatformLibraryOwnerAssign(ownerId=owner_id),
                        actor_id,
                    )
                    return "assigned"
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(assign_worker, library_ids))
        assert sorted(results) == ["assigned", "rejected"]
        with factory() as db:
            assert db.scalar(select(func.count(LibraryMembership.id))) == 1
            assert db.scalar(
                select(func.count(Library.id)).where(
                    Library.primary_owner_user_id == owner_id
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)


def test_postgres_rejects_stale_concurrent_suspend_reactivate() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, _owner_id = _seed_actor_and_owner(factory)
        with factory() as db:
            library = Library(
                code="STATUS-RACE",
                name="Status Race Library",
                contact_email="status-race@example.com",
                status=LibraryStatus.ACTIVE,
            )
            db.add(library)
            db.commit()
            library_id = library.id
            expected_updated_at = library.updated_at
        barrier = Barrier(2)

        def status_worker(target: LibraryStatus) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    change_library_status(
                        db,
                        library_id,
                        PlatformLibraryStatusUpdate(
                            status=target,
                            reason=("Concurrent review" if target == LibraryStatus.SUSPENDED else None),
                            expectedUpdatedAt=expected_updated_at,
                        ),
                        actor_id,
                    )
                    return target.value
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            suspend = executor.submit(status_worker, LibraryStatus.SUSPENDED)
            activate = executor.submit(status_worker, LibraryStatus.ACTIVE)
            results = [suspend.result(), activate.result()]
        assert sorted(results) == ["rejected", "suspended"]
        with factory() as db:
            library = db.get(Library, library_id)
            assert library.status == LibraryStatus.SUSPENDED
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action.in_(
                        ["platform.library.suspended", "platform.library.activated"]
                    )
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)
