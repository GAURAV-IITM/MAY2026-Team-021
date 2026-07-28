"""Owner seat-change request list and review API coverage."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import func, select

from app.models.audit import AuditLog
from app.models.enums import SeatRequestStatus
from app.models.seat import SeatAllocation, SeatChangeRequest
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _seed_request(client, session_factory, headers, *, status="pending"):
    seats = client.get("/api/v1/seats", headers=headers).json()["data"]["seats"]
    shifts = client.get(
        "/api/v1/shifts",
        params={"includeInactive": False},
        headers=headers,
    ).json()["data"]
    suffix = uuid.uuid4().hex[:8]
    student = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=False,
            email=f"seat-request-{suffix}@example.com",
            phone=f"91{suffix[:8].replace('a', '1').replace('b', '2').replace('c', '3').replace('d', '4').replace('e', '5').replace('f', '6')}",
        ),
        headers=headers,
    ).json()["data"]
    with session_factory() as db:
        seat_index = (
            db.scalar(select(func.count(SeatAllocation.id))) or 0
        ) % len(seats)
    allocation = client.post(
        "/api/v1/seat-allocations",
        json={
            "studentId": student["id"],
            "seatId": seats[seat_index]["id"],
            "shiftIds": [shifts[0]["id"]],
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=30)).isoformat(),
        },
        headers=headers,
    ).json()["data"]["allocations"][0]
    request_id = uuid.uuid4()
    with session_factory() as db:
        request = SeatChangeRequest(
            id=request_id,
            library_id=uuid.UUID(allocation["libraryId"]),
            student_id=uuid.UUID(student["id"]),
            request_number=f"REQ-{request_id.hex[:8]}",
            current_allocation_id=uuid.UUID(allocation["id"]),
            preferred_seat_id=uuid.UUID(
                seats[(seat_index + 1) % len(seats)]["id"]
            ),
            preferred_floor_id=uuid.UUID(
                seats[(seat_index + 1) % len(seats)]["floorId"]
            ),
            preferred_shift_id=uuid.UUID(shifts[-1]["id"]),
            reason="I need a quieter seat for focused examination preparation.",
            status=SeatRequestStatus(status),
        )
        if status != "pending":
            request.admin_note = "Decision already recorded."
            request.resolved_at = datetime.now(timezone.utc)
            request.reviewed_by_user_id = uuid.UUID(
                allocation["allocatedBy"]["id"]
            )
        db.add(request)
        db.commit()
    return {
        "id": str(request_id),
        "allocation": allocation,
        "student": student,
    }


def test_list_search_filter_pagination_and_summary(
    api,
    owner_headers,
) -> None:
    client, sessions = api
    pending = _seed_request(client, sessions, owner_headers)
    _seed_request(client, sessions, owner_headers, status="approved")

    response = client.get(
        "/api/v1/seat-requests",
        params={
            "status": "pending",
            "search": pending["student"]["enrollmentNumber"],
            "pageSize": 1,
        },
        headers=owner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["totalItems"] == 1
    assert payload["data"][0]["id"] == pending["id"]
    assert payload["data"][0]["currentAllocation"]["id"] == (
        pending["allocation"]["id"]
    )
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["pending"] == 1
    assert payload["summary"]["approved"] == 1


def test_approve_and_reject_without_changing_allocations(
    api,
    owner_headers,
) -> None:
    client, sessions = api
    approved_target = _seed_request(client, sessions, owner_headers)
    rejected_target = _seed_request(client, sessions, owner_headers)
    with sessions() as db:
        allocation_count = db.scalar(select(func.count(SeatAllocation.id)))
        allocation = db.get(
            SeatAllocation,
            uuid.UUID(approved_target["allocation"]["id"]),
        )
        original_facts = (
            allocation.seat_id,
            allocation.shift_id,
            allocation.status,
        )
        original_request = db.get(
            SeatChangeRequest,
            uuid.UUID(approved_target["id"]),
        )
        original_request_facts = (
            original_request.reason,
            original_request.preferred_seat_id,
            original_request.preferred_floor_id,
            original_request.preferred_shift_id,
        )

    approved = client.patch(
        f"/api/v1/seat-requests/{approved_target['id']}/review",
        json={"decision": "approved", "reviewNote": ""},
        headers={**owner_headers, "X-Request-ID": "seat-review-test"},
    )
    assert approved.status_code == 200
    assert approved.headers["x-request-id"] == "seat-review-test"
    assert approved.json()["data"]["status"] == "approved"
    assert approved.json()["data"]["reviewedBy"]["name"]
    assert approved.json()["data"]["reviewedAt"]
    assert approved.json()["data"]["resultingAllocationId"] is None
    assert "No seat allocation was changed" in approved.json()["message"]
    original_reviewer = approved.json()["data"]["reviewedBy"]["id"]
    original_reviewed_at = approved.json()["data"]["reviewedAt"]

    missing_note = client.patch(
        f"/api/v1/seat-requests/{rejected_target['id']}/review",
        json={"decision": "rejected", "reviewNote": "   "},
        headers=owner_headers,
    )
    assert missing_note.status_code == 422
    rejected = client.patch(
        f"/api/v1/seat-requests/{rejected_target['id']}/review",
        json={
            "decision": "rejected",
            "reviewNote": "The requested area is not available.",
        },
        headers=owner_headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rejected"

    repeated = client.patch(
        f"/api/v1/seat-requests/{approved_target['id']}/review",
        json={"decision": "rejected", "reviewNote": "Changed decision."},
        headers=owner_headers,
    )
    assert repeated.status_code == 409
    assert (
        repeated.json()["error"]["code"]
        == "SEAT_REQUEST_ALREADY_REVIEWED"
    )

    with sessions() as db:
        assert db.scalar(select(func.count(SeatAllocation.id))) == allocation_count
        unchanged = db.get(
            SeatAllocation,
            uuid.UUID(approved_target["allocation"]["id"]),
        )
        assert (
            unchanged.seat_id,
            unchanged.shift_id,
            unchanged.status,
        ) == original_facts
        request = db.get(
            SeatChangeRequest,
            uuid.UUID(approved_target["id"]),
        )
        assert (
            request.reason,
            request.preferred_seat_id,
            request.preferred_floor_id,
            request.preferred_shift_id,
        ) == original_request_facts
        assert str(request.reviewed_by_user_id) == original_reviewer
        expected_reviewed_at = datetime.fromisoformat(
            original_reviewed_at.replace("Z", "+00:00")
        )
        assert request.resolved_at.replace(tzinfo=timezone.utc) == (
            expected_reviewed_at
        )
        assert request.resulting_allocation_id is None
        assert db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.entity_id == approved_target["id"],
                AuditLog.action == "seat_change_request.approved",
            )
        ) == 1


def test_cross_tenant_review_is_hidden(api, owner_headers) -> None:
    client, sessions = api
    target = _seed_request(client, sessions, owner_headers)
    other = register(
        client,
        email="other.seat.request.owner@example.com",
        library_name="Other Seat Request Library",
    )
    response = client.patch(
        f"/api/v1/seat-requests/{target['id']}/review",
        json={"decision": "approved"},
        headers=bearer(other.json()["accessToken"]),
    )
    assert response.status_code == 404
    assert "student" not in response.json()["error"]["details"]


def test_missing_request_and_invalid_decision_use_structured_errors(
    api,
    owner_headers,
) -> None:
    client, _ = api
    missing = client.patch(
        f"/api/v1/seat-requests/{uuid.uuid4()}/review",
        json={"decision": "approved"},
        headers=owner_headers,
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "SEAT_REQUEST_NOT_FOUND"
    assert missing.json()["requestId"]

    invalid = client.patch(
        f"/api/v1/seat-requests/{uuid.uuid4()}/review",
        json={"decision": "pending"},
        headers=owner_headers,
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert invalid.json()["requestId"]


def test_seat_request_routes_require_library_staff(
    api,
    owner_headers,
) -> None:
    client, _ = api
    assert client.get("/api/v1/seat-requests").status_code == 401

    invited = client.post(
        "/api/v1/students",
        json=student_payload(
            email="seat.request.portal.student@example.com",
            phone="9876543216",
            sendInvitation=True,
        ),
        headers=owner_headers,
    )
    assert invited.status_code == 201
    student = invited.json()["data"]
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

    forbidden = client.get(
        "/api/v1/seat-requests",
        headers=bearer(login.json()["accessToken"]),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"
