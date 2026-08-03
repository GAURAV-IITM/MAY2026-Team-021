"""PostgreSQL transaction and concurrency evidence for platform settings."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers SQLAlchemy metadata
from app.core.exceptions import ApplicationError
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.enums import RoleName
from app.models.identity import Role, User, UserRole
from app.models.library import PlatformSetting
from app.schemas.platform import PlatformSettingsUpdate
from app.services.platform_settings import update_settings


POSTGRES_URL = os.getenv("TEST_POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Set TEST_POSTGRES_DATABASE_URL to run platform settings lock tests.",
)


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database():
    url = _normalize_url(POSTGRES_URL)
    schema = f"platform_settings_{uuid.uuid4().hex}"
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


def _seed_actor(factory) -> uuid.UUID:
    with factory() as db:
        role = Role(name=RoleName.SUPER_ADMIN, description="Platform admin")
        actor = User(
            email=f"settings-race-{uuid.uuid4().hex}@example.com",
            password_hash="not-used",
            full_name="Settings Admin",
            role_links=[UserRole(role=role)],
        )
        db.add(actor)
        db.commit()
        return actor.id


def test_postgres_atomic_multi_setting_update_and_upsert() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id = _seed_actor(factory)
        with factory() as db:
            first = update_settings(
                db,
                PlatformSettingsUpdate(
                    version=0,
                    allowLibraryRegistrations=False,
                    sessionTimeoutMinutes=90,
                    defaultTimezone="UTC",
                ),
                actor_id,
            )
            assert first.version == 1
        with factory() as db:
            second = update_settings(
                db,
                PlatformSettingsUpdate(
                    version=1,
                    sessionTimeoutMinutes=120,
                ),
                actor_id,
            )
            assert second.version == 2
            assert second.settings.session_timeout_minutes == 120
            assert db.scalar(
                select(func.count(PlatformSetting.id)).where(
                    PlatformSetting.key == "session_timeout_minutes"
                )
            ) == 1
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "platform.settings.updated"
                )
            ) == 2
    finally:
        _cleanup(schema, admin_engine, engine)


def test_postgres_rejects_one_of_two_concurrent_first_updates() -> None:
    schema, admin_engine, engine, factory = _database()
    try:
        actor_id = _seed_actor(factory)
        barrier = Barrier(2)

        def worker(timeout: int) -> str:
            with factory() as db:
                barrier.wait(timeout=10)
                try:
                    update_settings(
                        db,
                        PlatformSettingsUpdate(
                            version=0,
                            sessionTimeoutMinutes=timeout,
                        ),
                        actor_id,
                    )
                    return "updated"
                except ApplicationError:
                    return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, (60, 120)))
        assert sorted(results) == ["conflict", "updated"]
        with factory() as db:
            assert db.scalar(
                select(func.count(PlatformSetting.id)).where(
                    PlatformSetting.key == "session_timeout_minutes"
                )
            ) == 1
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "platform.settings.updated"
                )
            ) == 1
    finally:
        _cleanup(schema, admin_engine, engine)
