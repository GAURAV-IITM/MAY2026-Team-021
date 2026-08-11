"""PostgreSQL evidence for platform-owner locks and uniqueness rules."""
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
from app.models.identity import AccountInvitation, Role, User, UserRole
from app.models.library import Library
from app.schemas.platform import (
    PlatformOwnerAssignmentUpdate,
    PlatformOwnerInvite,
    PlatformOwnerStatusUpdate,
)
from app.services.platform import assign_owner, change_owner_status, invite_owner


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
    schema = f"platform_owner_{uuid.uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url,
        pool_size=8,
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


def _seed(factory):
    with factory() as db:
        admin_role = Role(name=RoleName.SUPER_ADMIN, description="Platform administrator")
        owner_role = Role(name=RoleName.LIBRARY_OWNER, description="Library owner")
        actor = User(
            email=f"owner-admin-{uuid.uuid4().hex}@example.com",
            password_hash="not-used",
            full_name="Platform Admin",
        )
        owner = User(
            email=f"owner-race-{uuid.uuid4().hex}@example.com",
            password_hash="not-used",
            full_name="Concurrent Owner",
        )
        actor.role_links.append(UserRole(role=admin_role))
        owner.role_links.append(UserRole(role=owner_role))
        libraries = [
            Library(
                code=f"OWNER-RACE-{index}-{uuid.uuid4().hex[:5]}",
                name=f"Owner Race Library {index} {uuid.uuid4().hex[:5]}",
                contact_email=f"owner-race-{index}-{uuid.uuid4().hex[:5]}@example.com",
                status=LibraryStatus.PENDING,
            )
            for index in range(2)
        ]
        db.add_all([actor, owner, *libraries])
        db.commit()
        return actor.id, owner.id, [library.id for library in libraries], owner.updated_at


def test_postgres_prevents_concurrent_owner_invitations() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, _owner_id, library_ids, _updated_at = _seed(factory)
        email = f"same-invite-{uuid.uuid4().hex}@example.com"
        barrier = Barrier(2)

        def invite_worker(library_id: uuid.UUID) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    invite_owner(
                        db,
                        PlatformOwnerInvite(
                            name="Concurrent Invitee",
                            email=email,
                            libraryId=library_id,
                        ),
                        actor_id,
                    )
                    return "invited"
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(invite_worker, library_ids))
        assert sorted(results) == ["invited", "rejected"]
        with factory() as db:
            assert db.scalar(
                select(func.count(AccountInvitation.id)).where(
                    AccountInvitation.email == email
                )
            ) == 1
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "platform.owner.invited"
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)


def test_postgres_rejects_stale_concurrent_owner_assignment() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, owner_id, library_ids, expected_updated_at = _seed(factory)
        barrier = Barrier(2)

        def assignment_worker(library_id: uuid.UUID) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    assign_owner(
                        db,
                        owner_id,
                        PlatformOwnerAssignmentUpdate(
                            libraryId=library_id,
                            expectedUpdatedAt=expected_updated_at,
                        ),
                        actor_id,
                    )
                    return "assigned"
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(assignment_worker, library_ids))
        assert sorted(results) == ["assigned", "rejected"]
        with factory() as db:
            assert db.scalar(
                select(func.count(Library.id)).where(
                    Library.primary_owner_user_id == owner_id
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)


def test_postgres_serializes_assignment_against_owner_suspension() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id, owner_id, library_ids, expected_updated_at = _seed(factory)
        barrier = Barrier(2)

        def assign_worker() -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    assign_owner(
                        db,
                        owner_id,
                        PlatformOwnerAssignmentUpdate(
                            libraryId=library_ids[0],
                            expectedUpdatedAt=expected_updated_at,
                        ),
                        actor_id,
                    )
                    return "assigned"
                except ApplicationError:
                    return "rejected"

        def suspend_worker() -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    change_owner_status(
                        db,
                        owner_id,
                        PlatformOwnerStatusUpdate(
                            status="suspended",
                            reason="Concurrent review",
                            expectedUpdatedAt=expected_updated_at,
                        ),
                        actor_id,
                    )
                    return "suspended"
                except ApplicationError:
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assignment = executor.submit(assign_worker)
            suspension = executor.submit(suspend_worker)
            results = [assignment.result(), suspension.result()]
        assert "rejected" in results
        assert len(set(results)) == 2
    finally:
        _cleanup(schema, admin_engine, engine)
