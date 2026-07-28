"""Owner announcement management API coverage."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import func, select

from app.models.announcement import Announcement
from app.models.audit import AuditLog
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _future(*, days: int = 0, hours: int = 0) -> str:
    return (
        datetime.now(timezone.utc)
        + timedelta(days=days, hours=hours)
    ).isoformat()


def _payload(**overrides):
    payload = {
        "title": "Library Closed on Sunday",
        "body": "The library will remain closed this Sunday for maintenance.",
        "category": "general",
        "priority": "normal",
        "audience": "all_students",
        "status": "draft",
        "scheduledAt": None,
        "expiresAt": None,
    }
    payload.update(overrides)
    return payload


def _create(client, headers, **overrides):
    return client.post(
        "/api/v1/announcements",
        json=_payload(**overrides),
        headers=headers,
    )


def test_create_list_search_filter_summary_and_audit(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    draft = _create(
        client,
        {**owner_headers, "X-Request-ID": "announcement-create-test"},
    )
    assert draft.status_code == 201
    assert draft.headers["x-request-id"] == "announcement-create-test"
    assert draft.json()["data"]["status"] == "draft"
    assert draft.json()["data"]["createdBy"]["name"]

    scheduled = _create(
        client,
        owner_headers,
        title="Fee Deadline Reminder",
        body="Please pay this month's library fee before the due date.",
        category="fees",
        priority="important",
        audience="pending_fee_students",
        status="scheduled",
        scheduledAt=_future(hours=3),
        expiresAt=_future(days=2),
    )
    assert scheduled.status_code == 201

    listed = client.get(
        "/api/v1/announcements",
        params={
            "search": "fee",
            "status": "scheduled",
            "category": "fees",
            "priority": "important",
            "audience": "pending_fee_students",
            "pageSize": 1,
        },
        headers=owner_headers,
    )
    assert listed.status_code == 200
    result = listed.json()
    assert result["meta"] == {
        "page": 1,
        "pageSize": 1,
        "totalItems": 1,
        "totalPages": 1,
    }
    assert result["data"][0]["title"] == "Fee Deadline Reminder"
    # Summary remains library-wide when filters are active.
    assert result["summary"]["total"] == 2
    assert result["summary"]["drafts"] == 1
    assert result["summary"]["scheduled"] == 1

    with testing_session() as db:
        audits = list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.action == "announcement.created"
                )
            )
        )
    assert len(audits) == 2
    assert audits[0].library_id is not None


def test_update_publish_archive_and_soft_delete_lifecycle(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    created = _create(client, owner_headers).json()["data"]

    updated = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={
            "title": "Updated Library Closure",
            "status": "scheduled",
            "scheduledAt": _future(hours=4),
            "expectedUpdatedAt": created["updatedAt"],
        },
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "scheduled"

    published = client.post(
        f"/api/v1/announcements/{created['id']}/publish",
        headers=owner_headers,
    )
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "published"
    assert published.json()["data"]["publishedAt"] is not None

    invalid_edit = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={"title": "Published content cannot be changed"},
        headers=owner_headers,
    )
    assert invalid_edit.status_code == 409
    assert (
        invalid_edit.json()["error"]["code"]
        == "ANNOUNCEMENT_INVALID_STATE_TRANSITION"
    )

    direct_delete = client.delete(
        f"/api/v1/announcements/{created['id']}",
        headers=owner_headers,
    )
    assert direct_delete.status_code == 409

    archived = client.post(
        f"/api/v1/announcements/{created['id']}/archive",
        json={"reason": "No longer relevant"},
        headers=owner_headers,
    )
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"
    assert archived.json()["data"]["archivedAt"] is not None

    deleted = client.delete(
        f"/api/v1/announcements/{created['id']}",
        headers=owner_headers,
    )
    assert deleted.status_code == 204
    missing = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={"title": "Cannot edit a deleted announcement"},
        headers=owner_headers,
    )
    assert missing.status_code == 404

    with testing_session() as db:
        record = db.scalar(
                select(Announcement).where(
                    Announcement.id == uuid.UUID(created["id"])
                )
        )
        assert record is not None
        assert record.deleted_at is not None
        actions = set(
            db.scalars(
                select(AuditLog.action).where(
                    AuditLog.entity_id == created["id"]
                )
            )
        )
    assert {
        "announcement.created",
        "announcement.updated",
        "announcement.published",
        "announcement.archived",
        "announcement.deleted",
    } <= actions


def test_date_validation_stale_update_role_and_tenant_isolation(
    api,
    owner_headers,
) -> None:
    client, _ = api
    past_schedule = _create(
        client,
        owner_headers,
        status="scheduled",
        scheduledAt=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    )
    assert past_schedule.status_code == 422
    assert (
        past_schedule.json()["error"]["code"]
        == "ANNOUNCEMENT_SCHEDULE_NOT_FUTURE"
    )

    invalid_expiry = _create(
        client,
        owner_headers,
        status="scheduled",
        scheduledAt=_future(days=2),
        expiresAt=_future(days=1),
    )
    assert invalid_expiry.status_code == 422
    assert (
        invalid_expiry.json()["error"]["code"]
        == "ANNOUNCEMENT_EXPIRY_BEFORE_PUBLISH"
    )

    created = _create(client, owner_headers).json()["data"]
    first_update = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={
            "title": "First valid announcement update",
            "expectedUpdatedAt": created["updatedAt"],
        },
        headers=owner_headers,
    )
    assert first_update.status_code == 200
    stale = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={
            "title": "Stale announcement update",
            "expectedUpdatedAt": created["updatedAt"],
        },
        headers=owner_headers,
    )
    assert stale.status_code == 409
    assert (
        stale.json()["error"]["code"]
        == "ANNOUNCEMENT_STATE_CHANGED"
    )

    second_owner = register(
        client,
        email="second.announcement.owner@example.com",
        library_name="Second Announcement Library",
    )
    assert second_owner.status_code == 201
    second_headers = bearer(second_owner.json()["accessToken"])
    hidden = client.patch(
        f"/api/v1/announcements/{created['id']}",
        json={"title": "Cross tenant update attempt"},
        headers=second_headers,
    )
    assert hidden.status_code == 404
    second_list = client.get(
        "/api/v1/announcements",
        headers=second_headers,
    )
    assert second_list.status_code == 200
    assert second_list.json()["summary"]["total"] == 0


def test_announcement_routes_require_library_staff(
    api,
    owner_headers,
) -> None:
    client, _ = api
    unauthenticated = client.get("/api/v1/announcements")
    assert unauthenticated.status_code == 401

    student_response = client.post(
        "/api/v1/students",
        json=student_payload(sendInvitation=True),
        headers=owner_headers,
    )
    assert student_response.status_code == 201
    student = student_response.json()["data"]
    token = parse_qs(
        urlsplit(student["invitationSetupUrl"]).query
    )["token"][0]
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )
    assert accepted.status_code == 200
    login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": student["email"],
            "password": "StudentPass123",
        },
    )
    assert login.status_code == 200
    student_headers = bearer(login.json()["accessToken"])

    forbidden = client.get(
        "/api/v1/announcements",
        headers=student_headers,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"
