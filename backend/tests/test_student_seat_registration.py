"""Student registration with transactional seat assignment coverage."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select

from app.models.enums import AllocationStatus
from app.models.seat import SeatAllocation
from app.models.student import Student
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _resources(client, headers):
    seats_response = client.get("/api/v1/seats", headers=headers)
    shifts_response = client.get(
        "/api/v1/shifts",
        params={"includeInactive": False},
        headers=headers,
    )
    assert seats_response.status_code == 200
    assert shifts_response.status_code == 200
    return (
        seats_response.json()["data"]["seats"],
        shifts_response.json()["data"],
    )


def _period() -> tuple[str, str]:
    start = date.today()
    return start.isoformat(), (start + timedelta(days=30)).isoformat()


def _allocation_payload(seat_id, shift_ids, **overrides):
    start_date, end_date = _period()
    payload = {
        "seatId": seat_id,
        "shiftIds": shift_ids,
        "startDate": start_date,
        "endDate": end_date,
        "notes": "Assigned during registration.",
    }
    payload.update(overrides)
    return payload


def test_registration_creates_student_invitation_and_allocations_atomically(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    seat = seats[0]
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    start_date, end_date = _period()

    before = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": [morning["id"]],
            "startDate": start_date,
            "endDate": end_date,
        },
        headers=owner_headers,
    )
    assert before.status_code == 200
    available_seat = next(
        item
        for item in before.json()["data"]["seats"]
        if item["seatId"] == seat["id"]
    )
    assert available_seat["isAvailable"] is True

    created = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=True,
            seatAllocation=_allocation_payload(
                seat["id"],
                [morning["id"]],
            ),
        ),
        headers=owner_headers,
    )
    assert created.status_code == 201
    student = created.json()["data"]
    assert student["seatNumber"] == seat["seatNumber"]
    assert student["activeShifts"] == [morning["id"]]
    assert student["activeShiftNames"] == ["Morning"]
    assignment = student["seatAssignments"][0]
    assert assignment == {
        "seatId": seat["id"],
        "seatNumber": seat["seatNumber"],
        "floorId": seat["floorId"],
        "floorName": seat["floorName"],
        "shiftIds": [morning["id"]],
        "shiftNames": ["Morning"],
        "startDate": start_date,
        "endDate": end_date,
        "status": "active",
        "closeReason": None,
        "previousAllocationId": None,
        "transferGroupId": assignment["transferGroupId"],
    }
    assert assignment["transferGroupId"] is not None
    assert student["invitationSetupUrl"]

    after = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": [morning["id"]],
            "startDate": start_date,
            "endDate": end_date,
        },
        headers=owner_headers,
    )
    occupied_seat = next(
        item
        for item in after.json()["data"]["seats"]
        if item["seatId"] == seat["id"]
    )
    assert occupied_seat["isAvailable"] is False
    assert occupied_seat["status"] == "allotted"
    assert occupied_seat["blockers"][0]["studentName"] == "Aarav Sharma"

    conflict = client.post(
        "/api/v1/students",
        json=student_payload(
            firstName="Diya",
            lastName="Patel",
            email="diya@example.com",
            phone="9876543212",
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seat["id"],
                [morning["id"]],
            ),
        ),
        headers=owner_headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "SEAT_ALLOCATION_CONFLICT"
    assert "Aarav Sharma" in conflict.json()["error"]["message"]

    with testing_session() as db:
        diya_count = db.scalar(
            select(func.count(Student.id)).where(
                Student.email == "diya@example.com"
            )
        )
        allocation_count = db.scalar(select(func.count(SeatAllocation.id)))
    assert diya_count == 0
    assert allocation_count == 1


def test_same_seat_can_be_registered_for_non_overlapping_shifts(
    api,
    owner_headers,
) -> None:
    client, _ = api
    seats, shifts = _resources(client, owner_headers)
    seat = seats[0]
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    afternoon = next(shift for shift in shifts if shift["name"] == "Afternoon")

    first = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=False,
            seatAllocation=_allocation_payload(seat["id"], [morning["id"]]),
        ),
        headers=owner_headers,
    )
    second = client.post(
        "/api/v1/students",
        json=student_payload(
            firstName="Ananya",
            lastName="Das",
            email="ananya@example.com",
            phone="9876543213",
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seat["id"],
                [afternoon["id"]],
            ),
        ),
        headers=owner_headers,
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["data"]["seatNumber"] == seat["seatNumber"]


def test_registration_rejects_overlapping_shifts_and_unavailable_seats(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    seat = seats[0]
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    office = client.post(
        "/api/v1/shifts",
        json={
            "name": "Office hours",
            "startTime": "09:00",
            "endTime": "17:00",
        },
        headers=owner_headers,
    ).json()["data"]

    overlapping = client.post(
        "/api/v1/students",
        json=student_payload(
            email="overlap@example.com",
            phone="9876543214",
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seat["id"],
                [morning["id"], office["id"]],
            ),
        ),
        headers=owner_headers,
    )
    assert overlapping.status_code == 422
    assert overlapping.json()["error"]["code"] == "ALLOCATION_SHIFTS_OVERLAP"

    maintenance = client.patch(
        f"/api/v1/seats/{seat['id']}/status",
        json={"status": "maintenance", "reason": "Repair"},
        headers=owner_headers,
    )
    assert maintenance.status_code == 200
    unavailable = client.post(
        "/api/v1/students",
        json=student_payload(
            email="maintenance@example.com",
            phone="9876543215",
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seat["id"],
                [morning["id"]],
            ),
        ),
        headers=owner_headers,
    )
    assert unavailable.status_code == 422
    assert (
        unavailable.json()["error"]["code"]
        == "SEAT_NOT_OPERATIONALLY_AVAILABLE"
    )

    with testing_session() as db:
        failed_students = db.scalar(
            select(func.count(Student.id)).where(
                Student.email.in_(
                    ["overlap@example.com", "maintenance@example.com"]
                )
            )
        )
    assert failed_students == 0


def test_registration_cannot_use_another_library_seat(
    api,
    owner_headers,
) -> None:
    client, _ = api
    first_library_seats, first_library_shifts = _resources(client, owner_headers)
    second_registration = register(
        client,
        libraryName="Second Library",
        email="second.owner@example.com",
        phone="9876543299",
    )
    second_headers = bearer(second_registration.json()["accessToken"])

    cross_tenant = client.post(
        "/api/v1/students",
        json=student_payload(
            email="second.student@example.com",
            phone="9876543216",
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                first_library_seats[0]["id"],
                [first_library_shifts[0]["id"]],
            ),
        ),
        headers=second_headers,
    )
    assert cross_tenant.status_code in {404, 422}
    assert cross_tenant.json()["error"]["code"] in {
        "SEAT_NOT_FOUND",
        "ALLOCATION_SHIFT_INVALID",
    }


def test_edit_student_updates_profile_and_replaces_allocation_with_history(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    afternoon = next(shift for shift in shifts if shift["name"] == "Afternoon")
    original_start = date.today() - timedelta(days=1)
    replacement_end = date.today() + timedelta(days=45)

    created = client.post(
        "/api/v1/students",
        json=student_payload(
            joiningDate=(date.today() - timedelta(days=10)).isoformat(),
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seats[0]["id"],
                [morning["id"]],
                startDate=original_start.isoformat(),
                endDate=replacement_end.isoformat(),
            ),
        ),
        headers=owner_headers,
    )
    assert created.status_code == 201
    student = created.json()["data"]
    student_uuid = uuid.UUID(student["id"])
    original_allocation_id = None
    with testing_session() as db:
        original_allocation_id = db.scalar(
            select(SeatAllocation.id).where(
                SeatAllocation.student_id == student_uuid
            )
        )

    own_seat_availability = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": [morning["id"]],
            "startDate": date.today().isoformat(),
            "endDate": replacement_end.isoformat(),
            "excludeStudentId": student["id"],
        },
        headers=owner_headers,
    )
    assert own_seat_availability.status_code == 200
    own_seat = next(
        seat
        for seat in own_seat_availability.json()["data"]["seats"]
        if seat["seatId"] == seats[0]["id"]
    )
    assert own_seat["isAvailable"] is True

    updated = client.patch(
        f"/api/v1/students/{student['id']}",
        json={
            "enrollmentNumber": student["enrollmentNumber"],
            "firstName": "Aarav Updated",
            "lastName": student["lastName"],
            "email": student["email"],
            "phone": student["phone"],
            "address": None,
            "guardianName": None,
            "guardianPhone": None,
            "dateOfBirth": None,
            "preferredLanguage": "en",
            "joiningDate": student["joiningDate"],
            "feeAmount": 1400,
            "status": "active",
            "notes": "Profile and allocation edited together.",
            "seatAllocationChange": {
                "action": "replace",
                "allocation": _allocation_payload(
                    seats[1]["id"],
                    [afternoon["id"]],
                    startDate=date.today().isoformat(),
                    endDate=replacement_end.isoformat(),
                ),
                "reason": "Moved to a quieter seat.",
            },
        },
        headers=owner_headers,
    )
    assert updated.status_code == 200
    response_student = updated.json()["data"]
    assert response_student["firstName"] == "Aarav Updated"
    assert response_student["feeAmount"] == 1400
    assert response_student["seatNumber"] == seats[1]["seatNumber"]
    assert response_student["activeShiftNames"] == ["Afternoon"]
    assert len(response_student["allocationHistory"]) == 2
    assert {
        item["status"]
        for item in response_student["allocationHistory"]
    } == {"active", "completed"}

    with testing_session() as db:
        allocations = list(
            db.scalars(
                select(SeatAllocation)
                .where(SeatAllocation.student_id == student_uuid)
            )
        )
    assert len(allocations) == 2
    original = next(
        allocation
        for allocation in allocations
        if allocation.id == original_allocation_id
    )
    replacement = next(
        allocation
        for allocation in allocations
        if allocation.id != original_allocation_id
    )
    assert original.status == AllocationStatus.COMPLETED
    assert original.end_date == date.today() - timedelta(days=1)
    assert original.close_reason == "Moved to a quieter seat."
    assert replacement.status == AllocationStatus.ACTIVE
    assert replacement.previous_allocation_id == original.id
    assert replacement.transfer_group_id is not None


def test_edit_student_can_remove_allocation_without_deleting_history(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    created = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=False,
            seatAllocation=_allocation_payload(
                seats[0]["id"],
                [morning["id"]],
            ),
        ),
        headers=owner_headers,
    )
    student = created.json()["data"]
    student_uuid = uuid.UUID(student["id"])

    removed = client.patch(
        f"/api/v1/students/{student['id']}",
        json={
            "seatAllocationChange": {
                "action": "remove",
                "reason": "Student no longer needs a fixed seat.",
            }
        },
        headers=owner_headers,
    )
    assert removed.status_code == 200
    assert removed.json()["data"]["seatNumber"] is None
    assert removed.json()["data"]["seatAssignments"] == []
    assert removed.json()["data"]["allocationHistory"][0]["status"] == "cancelled"

    with testing_session() as db:
        allocation = db.scalar(
            select(SeatAllocation).where(
                SeatAllocation.student_id == student_uuid
            )
        )
    assert allocation is not None
    assert allocation.status == AllocationStatus.CANCELLED
    assert allocation.close_reason == "Student no longer needs a fixed seat."


def test_failed_allocation_change_rolls_back_profile_and_current_allocation(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    seats, shifts = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    first = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=False,
            seatAllocation=_allocation_payload(seats[0]["id"], [morning["id"]]),
        ),
        headers=owner_headers,
    ).json()["data"]
    second = client.post(
        "/api/v1/students",
        json=student_payload(
            firstName="Ananya",
            lastName="Das",
            email="ananya@example.com",
            phone="9876543213",
            sendInvitation=False,
            seatAllocation=_allocation_payload(seats[1]["id"], [morning["id"]]),
        ),
        headers=owner_headers,
    )
    assert second.status_code == 201

    conflict = client.patch(
        f"/api/v1/students/{first['id']}",
        json={
            "firstName": "Should Roll Back",
            "seatAllocationChange": {
                "action": "replace",
                "allocation": _allocation_payload(
                    seats[1]["id"],
                    [morning["id"]],
                ),
                "reason": "Attempt conflicting transfer.",
            },
        },
        headers=owner_headers,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "SEAT_ALLOCATION_CONFLICT"

    unchanged = client.get(
        f"/api/v1/students/{first['id']}",
        headers=owner_headers,
    ).json()["data"]
    assert unchanged["firstName"] == "Aarav"
    assert unchanged["seatNumber"] == seats[0]["seatNumber"]
    first_student_uuid = uuid.UUID(first["id"])
    with testing_session() as db:
        first_allocations = list(
            db.scalars(
                select(SeatAllocation).where(
                    SeatAllocation.student_id == first_student_uuid
                )
            )
        )
    assert len(first_allocations) == 1
    assert first_allocations[0].status == AllocationStatus.ACTIVE
