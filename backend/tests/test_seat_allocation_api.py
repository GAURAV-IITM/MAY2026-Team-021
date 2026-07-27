"""Standalone seat availability and allocation lifecycle API coverage."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import func, select

from app.models.audit import AuditLog
from app.models.enums import AllocationStatus
from app.models.seat import SeatAllocation
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _resources(client, headers):
    seats = client.get("/api/v1/seats", headers=headers).json()["data"]["seats"]
    shifts = client.get(
        "/api/v1/shifts",
        params={"includeInactive": False},
        headers=headers,
    ).json()["data"]
    return seats, shifts


def _create_student(client, headers, **overrides):
    response = client.post(
        "/api/v1/students",
        json=student_payload(sendInvitation=False, **overrides),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


def _allocation_payload(student_id, seat_id, shift_ids, **overrides):
    payload = {
        "studentId": student_id,
        "seatId": seat_id,
        "shiftIds": shift_ids,
        "startDate": date.today().isoformat(),
        "endDate": (date.today() + timedelta(days=30)).isoformat(),
        "notes": "Lifecycle API test.",
    }
    payload.update(overrides)
    return payload


def test_multi_shift_create_list_close_history_and_audit(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    evening = next(shift for shift in shifts if shift["name"] == "Evening")
    student = _create_student(client, owner_headers)

    created = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            student["id"],
            seats[0]["id"],
            [morning["id"], evening["id"]],
        ),
        headers={**owner_headers, "X-Request-ID": "allocation-create-test"},
    )
    assert created.status_code == 201
    assert created.headers["x-request-id"] == "allocation-create-test"
    result = created.json()["data"]
    assert result["allocationCount"] == 2
    assert len(result["allocations"]) == 2
    assert {
        item["shift"]["name"]
        for item in result["allocations"]
    } == {"Morning", "Evening"}
    assert len(
        {item["transferGroupId"] for item in result["allocations"]}
    ) == 1

    listed = client.get(
        "/api/v1/seat-allocations",
        params={
            "studentId": student["id"],
            "status": "active",
            "search": seats[0]["seatNumber"],
            "sortBy": "shiftName",
            "sortOrder": "asc",
        },
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["meta"]["totalItems"] == 2
    assert listed.json()["data"][0]["seat"]["seatNumber"] == seats[0]["seatNumber"]

    first, second = result["allocations"]
    completed = client.patch(
        f"/api/v1/seat-allocations/{first['id']}/status",
        json={
            "status": "completed",
            "effectiveEndDate": date.today().isoformat(),
            "closeReason": "Allocation period completed.",
        },
        headers=owner_headers,
    )
    cancelled = client.patch(
        f"/api/v1/seat-allocations/{second['id']}/status",
        json={
            "status": "cancelled",
            "effectiveEndDate": date.today().isoformat(),
            "closeReason": "Student cancelled this shift.",
        },
        headers=owner_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "completed"
    assert completed.json()["data"]["closedBy"]["name"]
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    repeated = client.patch(
        f"/api/v1/seat-allocations/{first['id']}/status",
        json={
            "status": "cancelled",
            "closeReason": "Repeated close.",
        },
        headers=owner_headers,
    )
    assert repeated.status_code == 409
    assert repeated.json()["error"]["code"] == "ALLOCATION_ALREADY_CLOSED"

    history = client.get(
        "/api/v1/seat-allocations",
        params={"studentId": student["id"]},
        headers=owner_headers,
    ).json()
    assert history["meta"]["totalItems"] == 2
    assert {item["status"] for item in history["data"]} == {
        "completed",
        "cancelled",
    }
    available_after_close = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": first["shift"]["id"],
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=30)).isoformat(),
        },
        headers=owner_headers,
    ).json()["data"]
    closed_seat = next(
        seat
        for seat in available_after_close["seats"]
        if seat["seatId"] == first["seat"]["id"]
    )
    assert closed_seat["status"] == "available"

    with testing_session() as db:
        audit_actions = set(
            db.scalars(
                select(AuditLog.action).where(
                    AuditLog.entity_type.in_(
                        ["seat_allocation", "seat_allocation_group"]
                    )
                )
            )
        )
    assert {
        "seat_allocation.created",
        "seat_allocation.completed",
        "seat_allocation.cancelled",
    }.issubset(audit_actions)


def test_conflicts_atomicity_status_precedence_and_consecutive_dates(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    afternoon = next(shift for shift in shifts if shift["name"] == "Afternoon")
    first_student = _create_student(client, owner_headers)
    second_student = _create_student(
        client,
        owner_headers,
        firstName="Ananya",
        lastName="Das",
        email="ananya@example.com",
        phone="9876543213",
    )
    first_end = date.today() + timedelta(days=10)

    first = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            first_student["id"],
            seats[0]["id"],
            [morning["id"]],
            endDate=first_end.isoformat(),
        ),
        headers=owner_headers,
    )
    assert first.status_code == 201

    seat_conflict = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            second_student["id"],
            seats[0]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert seat_conflict.status_code == 409
    assert seat_conflict.json()["error"]["code"] == "SEAT_ALLOCATION_CONFLICT"

    student_conflict = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            first_student["id"],
            seats[1]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert student_conflict.status_code == 409
    assert (
        student_conflict.json()["error"]["code"]
        == "STUDENT_ALLOCATION_CONFLICT"
    )

    consecutive = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            second_student["id"],
            seats[0]["id"],
            [morning["id"]],
            startDate=(first_end + timedelta(days=1)).isoformat(),
            endDate=(first_end + timedelta(days=20)).isoformat(),
        ),
        headers=owner_headers,
    )
    assert consecutive.status_code == 201

    office = client.post(
        "/api/v1/shifts",
        json={"name": "Office", "startTime": "09:00", "endTime": "17:00"},
        headers=owner_headers,
    ).json()["data"]
    with testing_session() as db:
        audit_count_before_failure = db.scalar(
            select(func.count(AuditLog.id))
        )
    overlapping_selection = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            second_student["id"],
            seats[2]["id"],
            [morning["id"], office["id"], afternoon["id"]],
        ),
        headers=owner_headers,
    )
    assert overlapping_selection.status_code == 422
    assert (
        overlapping_selection.json()["error"]["code"]
        == "ALLOCATION_SHIFTS_OVERLAP"
    )
    with testing_session() as db:
        created_on_third_seat = db.scalar(
            select(func.count(SeatAllocation.id)).where(
                SeatAllocation.seat_id == uuid.UUID(seats[2]["id"])
            )
        )
        audit_count_after_failure = db.scalar(
            select(func.count(AuditLog.id))
        )
    assert created_on_third_seat == 0
    assert audit_count_after_failure == audit_count_before_failure

    maintenance = client.patch(
        f"/api/v1/seats/{seats[3]['id']}/status",
        json={"status": "maintenance", "reason": "Repair"},
        headers=owner_headers,
    )
    blocked = client.patch(
        f"/api/v1/seats/{seats[4]['id']}/status",
        json={"status": "blocked", "reason": "Admin restriction"},
        headers=owner_headers,
    )
    assert maintenance.status_code == 200
    assert blocked.status_code == 200
    availability = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": morning["id"],
            "startDate": date.today().isoformat(),
        },
        headers=owner_headers,
    ).json()["data"]
    by_id = {seat["seatId"]: seat for seat in availability["seats"]}
    assert by_id[seats[3]["id"]]["status"] == "maintenance"
    assert by_id[seats[4]["id"]]["status"] == "physically_blocked"
    assert availability["summary"]["maintenance"] == 1
    assert availability["summary"]["physicallyBlocked"] == 1


def test_snapshot_history_auth_and_tenant_isolation(api, owner_headers) -> None:
    client, _ = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    student = _create_student(client, owner_headers)
    created = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            student["id"],
            seats[0]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert created.status_code == 201

    other_floor = client.post(
        "/api/v1/floors",
        json={
            "name": "Historical Move Target",
            "code": "HMT",
            "levelNumber": 4,
            "sortOrder": 4,
        },
        headers=owner_headers,
    ).json()["data"]
    renamed = client.patch(
        f"/api/v1/seats/{seats[0]['id']}",
        json={
            "seatNumber": "RENAMED-01",
            "floorId": other_floor["id"],
        },
        headers=owner_headers,
    )
    assert renamed.status_code == 200
    history = client.get(
        "/api/v1/seat-allocations",
        params={"studentId": student["id"]},
        headers=owner_headers,
    )
    historical_seat = history.json()["data"][0]["seat"]
    assert historical_seat["seatNumber"] == seats[0]["seatNumber"]
    assert historical_seat["floorId"] == seats[0]["floorId"]
    assert historical_seat["floorName"] == seats[0]["floorName"]

    unauthenticated = client.get("/api/v1/seat-allocations")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["requestId"]

    second_registration = register(
        client,
        libraryName="Second Library",
        email="second.owner@example.com",
        phone="9876543299",
    )
    second_headers = bearer(second_registration.json()["accessToken"])
    hidden = client.get(
        "/api/v1/seat-allocations",
        params={"studentId": student["id"]},
        headers=second_headers,
    )
    assert hidden.status_code == 200
    assert hidden.json()["data"] == []

    cross_tenant = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            student["id"],
            seats[1]["id"],
            [morning["id"]],
        ),
        headers=second_headers,
    )
    assert cross_tenant.status_code == 404
    assert cross_tenant.json()["error"]["code"] == "STUDENT_NOT_FOUND"

    second_seats, second_shifts = _resources(client, second_headers)
    second_morning = next(
        shift for shift in second_shifts if shift["name"] == "Morning"
    )
    second_student = _create_student(
        client,
        second_headers,
        email="second.student@example.com",
        phone="9876543298",
    )
    foreign_seat = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            second_student["id"],
            seats[1]["id"],
            [second_morning["id"]],
        ),
        headers=second_headers,
    )
    assert foreign_seat.status_code == 404
    assert foreign_seat.json()["error"]["code"] == "SEAT_NOT_FOUND"

    foreign_shift = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            second_student["id"],
            second_seats[0]["id"],
            [morning["id"]],
        ),
        headers=second_headers,
    )
    assert foreign_shift.status_code == 422
    assert foreign_shift.json()["error"]["code"] == "ALLOCATION_SHIFT_INVALID"


def test_student_role_and_ineligible_resources_are_rejected(
    api,
    owner_headers,
) -> None:
    client, _ = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    invited = client.post(
        "/api/v1/students",
        json=student_payload(
            email="portal.student@example.com",
            phone="9876543218",
            sendInvitation=True,
        ),
        headers=owner_headers,
    ).json()["data"]
    token = parse_qs(
        urlsplit(invited["invitationSetupUrl"]).query
    )["token"][0]
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )
    assert accepted.status_code == 200
    student_login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": "portal.student@example.com",
            "password": "StudentPass123",
        },
    )
    student_headers = bearer(student_login.json()["accessToken"])
    forbidden = client.get(
        "/api/v1/seat-allocations",
        headers=student_headers,
    )
    assert forbidden.status_code == 403

    inactive = _create_student(
        client,
        owner_headers,
        firstName="Inactive",
        email="inactive.allocation@example.com",
        phone="9876543217",
        status="inactive",
    )
    inactive_result = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            inactive["id"],
            seats[1]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert inactive_result.status_code == 422
    assert inactive_result.json()["error"]["code"] == "STUDENT_NOT_ACTIVE"

    duplicate_shifts = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            invited["id"],
            seats[1]["id"],
            [morning["id"], morning["id"]],
        ),
        headers=owner_headers,
    )
    assert duplicate_shifts.status_code == 422
    assert duplicate_shifts.json()["error"]["code"] == "VALIDATION_ERROR"

    for index, physical_status in ((2, "maintenance"), (3, "blocked")):
        status_response = client.patch(
            f"/api/v1/seats/{seats[index]['id']}/status",
            json={"status": physical_status, "reason": "Eligibility test"},
            headers=owner_headers,
        )
        assert status_response.status_code == 200
        unavailable_seat = client.post(
            "/api/v1/seat-allocations",
            json=_allocation_payload(
                invited["id"],
                seats[index]["id"],
                [morning["id"]],
            ),
            headers=owner_headers,
        )
        assert unavailable_seat.status_code == 422
        assert (
            unavailable_seat.json()["error"]["code"]
            == "SEAT_NOT_OPERATIONALLY_AVAILABLE"
        )

    deleted_seat = client.delete(
        f"/api/v1/seats/{seats[4]['id']}",
        headers=owner_headers,
    )
    assert deleted_seat.status_code == 200
    deleted_seat_result = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            invited["id"],
            seats[4]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert deleted_seat_result.status_code == 404
    assert deleted_seat_result.json()["error"]["code"] == "SEAT_NOT_FOUND"

    deleted_student = _create_student(
        client,
        owner_headers,
        firstName="Deleted",
        email="deleted.allocation@example.com",
        phone="9876543216",
    )
    deleted_student_response = client.delete(
        f"/api/v1/students/{deleted_student['id']}",
        headers=owner_headers,
    )
    assert deleted_student_response.status_code == 200
    deleted_student_result = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            deleted_student["id"],
            seats[5]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert deleted_student_result.status_code == 404
    assert deleted_student_result.json()["error"]["code"] == "STUDENT_NOT_FOUND"

    temporary_shift = client.post(
        "/api/v1/shifts",
        json={
            "name": "Temporary Shift",
            "startTime": "02:00",
            "endTime": "04:00",
        },
        headers=owner_headers,
    ).json()["data"]
    deleted_shift = client.delete(
        f"/api/v1/shifts/{temporary_shift['id']}",
        headers=owner_headers,
    )
    assert deleted_shift.status_code == 200
    deleted_shift_result = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            invited["id"],
            seats[6]["id"],
            [temporary_shift["id"]],
        ),
        headers=owner_headers,
    )
    assert deleted_shift_result.status_code == 422
    assert deleted_shift_result.json()["error"]["code"] == "ALLOCATION_SHIFT_INVALID"

    disabled = client.patch(
        f"/api/v1/shifts/{morning['id']}/status",
        json={"isEnabled": False},
        headers=owner_headers,
    )
    assert disabled.status_code == 200
    disabled_shift = client.post(
        "/api/v1/seat-allocations",
        json=_allocation_payload(
            invited["id"],
            seats[1]["id"],
            [morning["id"]],
        ),
        headers=owner_headers,
    )
    assert disabled_shift.status_code == 422
    assert disabled_shift.json()["error"]["code"] == "ALLOCATION_SHIFT_INVALID"
