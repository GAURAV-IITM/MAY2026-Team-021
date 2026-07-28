"""PostgreSQL evidence for announcement lifecycle row locks."""
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
from app.models.announcement import Announcement
from app.models.audit import AuditLog
from app.models.enums import (
    AnnouncementAudience,
    AnnouncementPriority,
    AnnouncementStatus,
    LibraryStatus,
)
from app.models.identity import User
from app.models.library import Library
from app.services.announcement import (
    delete_announcement,
    publish_announcement,
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


def _seed(session_factory):
    with session_factory() as db:
        suffix = uuid.uuid4().hex[:8]
        library = Library(
            code=f"ANN-{suffix}",
            name="Announcement Lock Test Library",
            contact_email=f"announcement-lock-{suffix}@example.com",
            status=LibraryStatus.ACTIVE,
        )
        actor = User(
            email=f"announcement-owner-{suffix}@example.com",
            password_hash="not-used",
            full_name="Announcement Lock Owner",
        )
        db.add_all([library, actor])
        db.flush()
        library.primary_owner_user_id = actor.id
        announcement = Announcement(
            library_id=library.id,
            title="Concurrent publish announcement",
            body="Only one concurrent request should publish this announcement.",
            category="general",
            priority=AnnouncementPriority.NORMAL,
            audience=AnnouncementAudience.ALL_STUDENTS,
            status=AnnouncementStatus.DRAFT,
            author_user_id=actor.id,
        )
        db.add(announcement)
        db.commit()
        return library.id, actor.id, announcement.id


def test_postgres_serializes_concurrent_publish_commands() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"announcement_lock_{uuid.uuid4().hex}"
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
        library_id, actor_id, announcement_id = _seed(session_factory)
        barrier = Barrier(2)

        def publish_worker() -> str:
            with session_factory() as db:
                barrier.wait(timeout=10)
                try:
                    publish_announcement(
                        db,
                        library_id,
                        announcement_id,
                        actor_id,
                    )
                    return "published"
                except ApplicationError:
                    db.rollback()
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(lambda _: publish_worker(), range(2))
            )
        assert sorted(results) == ["published", "rejected"]

        with session_factory() as db:
            announcement = db.get(Announcement, announcement_id)
            assert announcement is not None
            assert announcement.status == AnnouncementStatus.PUBLISHED
            assert announcement.published_at is not None
            assert db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "announcement.published"
                )
            ) == 1
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()


def test_postgres_serializes_publish_and_delete_race() -> None:
    url = _normalize_url(POSTGRES_URL)
    schema = f"announcement_race_{uuid.uuid4().hex}"
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
        library_id, actor_id, announcement_id = _seed(session_factory)
        barrier = Barrier(2)

        def run_publish() -> str:
            with session_factory() as db:
                barrier.wait(timeout=10)
                try:
                    publish_announcement(
                        db,
                        library_id,
                        announcement_id,
                        actor_id,
                    )
                    return "published"
                except ApplicationError:
                    db.rollback()
                    return "rejected"

        def run_delete() -> str:
            with session_factory() as db:
                barrier.wait(timeout=10)
                try:
                    delete_announcement(
                        db,
                        library_id,
                        announcement_id,
                        actor_id,
                    )
                    return "deleted"
                except ApplicationError:
                    db.rollback()
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            publish_future = executor.submit(run_publish)
            delete_future = executor.submit(run_delete)
            results = [publish_future.result(), delete_future.result()]
        assert "rejected" in results
        assert len({"published", "deleted"} & set(results)) == 1

        with session_factory() as db:
            announcement = db.get(Announcement, announcement_id)
            assert announcement is not None
            if "published" in results:
                assert announcement.status == AnnouncementStatus.PUBLISHED
                assert announcement.deleted_at is None
            else:
                assert announcement.status == AnnouncementStatus.DRAFT
                assert announcement.deleted_at is not None
            successful_actions = db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action.in_(
                        [
                            "announcement.published",
                            "announcement.deleted",
                        ]
                    )
                )
            )
            assert successful_actions == 1
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            )
        admin_engine.dispose()
