from __future__ import annotations

import uuid
from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit
import pytest
from sqlalchemy import select, func

from app.models.enums import AllocationStatus, AnnouncementPriority, AnnouncementStatus, FeeStatus, PaymentTransactionStatus, RoleName, SeatRequestStatus, StudentStatus
from app.models.student import Student
from app.models.payment import FeeRecord, PaymentTransaction
from app.models.announcement import Announcement, AnnouncementRead
from app.models.seat import SeatChangeRequest, Shift, Seat
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _create_student_user(client, owner_headers, email="stu@example.com", phone="9876543219"):
    # Register student via staff API
    res = client.post(
        "/api/v1/students",
        json=student_payload(
            firstName="Portal",
            lastName="Student",
            email=email,
            phone=phone,
            sendInvitation=True,
        ),
        headers=owner_headers,
    )
    assert res.status_code == 201
    student_data = res.json()["data"]
    setup_url = student_data["invitationSetupUrl"]
    token = parse_qs(urlsplit(setup_url).query)["token"][0]

    # Accept invitation
    client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )

    # Login
    login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": email,
            "password": "StudentPass123",
        },
    )
    assert login.status_code == 200
    access_token = login.json()["accessToken"]
    return student_data, bearer(access_token)


def test_student_profile_get_and_patch(api, owner_headers):
    client, testing_session = api
    student_data, student_headers = _create_student_user(client, owner_headers)

    # GET /me profile
    profile_res = client.get("/api/v1/students/me", headers=student_headers)
    assert profile_res.status_code == 200
    profile = profile_res.json()["data"]
    assert profile["firstName"] == "Portal"
    assert profile["lastName"] == "Student"

    # PATCH /me profile - success for whitelisted
    update_res = client.patch(
        "/api/v1/students/me",
        json={"phone": "9876543210", "address": "123 Street Name"},
        headers=student_headers,
    )
    assert update_res.status_code == 200
    updated_profile = update_res.json()["data"]
    assert updated_profile["phone"] == "9876543210"

    # PATCH /me profile - failure for forbidden fields
    forbidden_res = client.patch(
        "/api/v1/students/me",
        json={"firstName": "Portal", "status": "active"},
        headers=student_headers,
    )
    assert forbidden_res.status_code == 422


def test_student_status_access_blocks(api, owner_headers):
    client, testing_session = api
    student_data, student_headers = _create_student_user(client, owner_headers, "status@example.com", "9876543218")

    # Set student to SUSPENDED via DB
    with testing_session() as db:
        student = db.get(Student, uuid.UUID(student_data["id"]))
        student.status = StudentStatus.SUSPENDED
        db.commit()

    # GET /me profile should fail with 403 Forbidden
    suspended_res = client.get("/api/v1/students/me", headers=student_headers)
    assert suspended_res.status_code == 403
    assert suspended_res.json()["error"]["code"] == "STUDENT_SUSPENDED"

    # Set student to INACTIVE via DB
    with testing_session() as db:
        student = db.get(Student, uuid.UUID(student_data["id"]))
        student.status = StudentStatus.INACTIVE
        db.commit()

    # GET /me profile should succeed
    inactive_get_res = client.get("/api/v1/students/me", headers=student_headers)
    assert inactive_get_res.status_code == 200

    # PATCH /me profile should fail
    inactive_patch_res = client.patch(
        "/api/v1/students/me",
        json={"phone": "1111111111"},
        headers=student_headers,
    )
    assert inactive_patch_res.status_code == 403
    assert inactive_patch_res.json()["error"]["code"] == "INACTIVE_STUDENT_ACCESS_DENIED"


def test_student_seat_allocations(api, owner_headers):
    client, testing_session = api
    student_data, student_headers = _create_student_user(client, owner_headers, "seat@example.com", "9876543217")

    # GET /seat-allocations/me
    res = client.get("/api/v1/seat-allocations/me", headers=student_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    # Unallocated student
    assert data["seat"] is None
    assert len(data["allocations"]) == 0


def test_student_announcements_feed_and_read(api, owner_headers):
    client, testing_session = api
    student_data, student_headers = _create_student_user(client, owner_headers, "ann@example.com", "9876543216")

    # Create published announcement in library
    with testing_session() as db:
        from app.models.student import Student
        student = db.get(Student, uuid.UUID(student_data["id"]))
        
        ann = Announcement(
            library_id=student.library_id,
            title="Important Announcement",
            body="This is a test announcement body.",
            category="general",
            priority=AnnouncementPriority.IMPORTANT,
            status=AnnouncementStatus.PUBLISHED,
            published_at=func.now(),
        )
        db.add(ann)
        db.commit()
        ann_id = ann.id

    # GET /announcements/feed
    feed_res = client.get("/api/v1/announcements/feed", headers=student_headers)
    assert feed_res.status_code == 200
    feed = feed_res.json()["data"]["announcements"]
    assert len(feed) >= 1
    assert feed[0]["title"] == "Important Announcement"
    assert feed[0]["isRead"] is False

    # POST /feed/{id}/read
    read_res = client.post(
        f"/api/v1/announcements/feed/{ann_id}/read",
        headers=student_headers,
    )
    assert read_res.status_code == 200
    assert read_res.json()["data"]["isRead"] is True

    # GET /announcements/feed again to verify isRead is True
    feed_res2 = client.get("/api/v1/announcements/feed", headers=student_headers)
    feed2 = feed_res2.json()["data"]["announcements"]
    assert feed2[0]["isRead"] is True


def test_student_seat_change_requests(api, owner_headers):
    client, testing_session = api
    student_data, student_headers = _create_student_user(client, owner_headers, "req@example.com", "9876543215")

    # Retrieve active shifts
    with testing_session() as db:
        from app.models.student import Student
        student = db.get(Student, uuid.UUID(student_data["id"]))
        shifts = db.scalars(
            select(Shift).where(
                Shift.library_id == student.library_id,
                Shift.is_active == True,
                Shift.deleted_at.is_(None),
            )
        ).all()
        shift_id = shifts[0].id

    # GET /seat-requests/me
    list_res = client.get("/api/v1/seat-requests/me", headers=student_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]["requests"]) == 0
    assert len(list_res.json()["data"]["shifts"]) > 0

    # POST /seat-requests/me
    create_res = client.post(
        "/api/v1/seat-requests/me",
        json={
            "preferredShiftId": str(shift_id),
            "reason": "This is a long enough reason text to satisfy validation rules.",
        },
        headers=student_headers,
    )
    assert create_res.status_code == 200
    req_data = create_res.json()["data"]
    assert req_data["status"] == "pending"

    # Try creating duplicate pending request
    duplicate_res = client.post(
        "/api/v1/seat-requests/me",
        json={
            "preferredShiftId": str(shift_id),
            "reason": "Another long enough reason text to satisfy validation rules.",
        },
        headers=student_headers,
    )
    assert duplicate_res.status_code == 409

    # Cancel request
    cancel_res = client.patch(
        f"/api/v1/seat-requests/me/{req_data['id']}/cancel",
        headers=student_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"
