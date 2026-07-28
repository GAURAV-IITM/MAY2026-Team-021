"""Owner dashboard/report API reconciliation and isolation coverage."""
from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit

from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _create_student(client, headers, **overrides):
    response = client.post(
        "/api/v1/students",
        json=student_payload(
            joiningDate=date.today().replace(day=1).isoformat(),
            sendInvitation=False,
            **overrides,
        ),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


def _resources(client, headers):
    seats = client.get("/api/v1/seats", headers=headers).json()["data"]["seats"]
    shifts = client.get(
        "/api/v1/shifts",
        params={"includeInactive": False},
        headers=headers,
    ).json()["data"]
    floors = client.get("/api/v1/floors", headers=headers).json()["data"]
    return seats, shifts, floors


def _allocate(client, headers, student_id, seat_id, shift_id):
    response = client.post(
        "/api/v1/seat-allocations",
        json={
            "studentId": student_id,
            "seatId": seat_id,
            "shiftIds": [shift_id],
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Report reconciliation allocation.",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["allocations"][0]


def _record(client, headers, fee_id, amount, reference):
    response = client.post(
        f"/api/v1/payments/{fee_id}/transactions",
        json={
            "amount": amount,
            "method": "upi",
            "referenceNumber": reference,
        },
        headers=headers,
    )
    assert response.status_code == 201


def test_dashboard_and_reports_reconcile_with_source_apis(
    api,
    owner_headers,
) -> None:
    client, _ = api
    month = _month_key(date.today())
    first = _create_student(client, owner_headers, feeAmount=1000)
    second = _create_student(
        client,
        owner_headers,
        firstName="Ananya",
        lastName="Das",
        email="ananya.reports@example.com",
        phone="9876543222",
        feeAmount=1000,
    )
    seats, shifts, floors = _resources(client, owner_headers)
    morning = next(shift for shift in shifts if shift["name"] == "Morning")
    _allocate(
        client,
        owner_headers,
        first["id"],
        seats[0]["id"],
        morning["id"],
    )
    maintenance = client.patch(
        f"/api/v1/seats/{seats[1]['id']}/status",
        json={"status": "maintenance", "reason": "Report test"},
        headers=owner_headers,
    )
    blocked = client.patch(
        f"/api/v1/seats/{seats[2]['id']}/status",
        json={"status": "blocked", "reason": "Report test"},
        headers=owner_headers,
    )
    assert maintenance.status_code == blocked.status_code == 200
    second_floor = client.post(
        "/api/v1/floors",
        json={
            "name": "Report Floor 2",
            "code": "RF2",
            "levelNumber": 2,
            "sortOrder": 2,
        },
        headers=owner_headers,
    )
    assert second_floor.status_code == 201
    second_seat = client.post(
        "/api/v1/seats",
        json={
            "seatNumber": "RF2-01",
            "floorId": second_floor.json()["data"]["id"],
            "seatType": "standard",
            "status": "available",
        },
        headers=owner_headers,
    )
    assert second_seat.status_code == 201

    generated = client.post(
        "/api/v1/payments/monthly-generation",
        json={"month": month},
        headers=owner_headers,
    )
    assert generated.status_code == 201
    fees = {
        item["student"]["id"]: item
        for item in generated.json()["data"]["createdPayments"]
    }
    _record(client, owner_headers, fees[first["id"]]["id"], "1000.00", "REPORT-A")
    _record(client, owner_headers, fees[second["id"]]["id"], "300.00", "REPORT-B")

    students = client.get(
        "/api/v1/students",
        params={"pageSize": 100},
        headers=owner_headers,
    ).json()
    active_students = client.get(
        "/api/v1/students",
        params={"status": "active", "pageSize": 100},
        headers=owner_headers,
    ).json()
    payments = client.get(
        "/api/v1/payments",
        params={"month": month, "pageSize": 100},
        headers=owner_headers,
    ).json()
    availability = client.get(
        "/api/v1/seat-allocations/availability",
        params={
            "shiftId": morning["id"],
            "startDate": date.today().isoformat(),
            "endDate": date.today().isoformat(),
        },
        headers=owner_headers,
    ).json()["data"]["summary"]

    dashboard_response = client.get(
        "/api/v1/reports/dashboard",
        params={"date": date.today().isoformat(), "billingMonth": month},
        headers={**owner_headers, "X-Request-ID": "dashboard-report-test"},
    )
    assert dashboard_response.status_code == 200
    assert dashboard_response.headers["x-request-id"] == "dashboard-report-test"
    dashboard = dashboard_response.json()["data"]
    assert dashboard["metrics"]["totalStudents"] == students["meta"]["totalItems"]
    assert (
        dashboard["metrics"]["activeStudents"]
        == active_students["meta"]["totalItems"]
    )
    assert (
        dashboard["metrics"]["pendingAmount"]
        == payments["summary"]["totalPendingAmount"]
        == "700.00"
    )
    morning_dashboard = next(
        item
        for item in dashboard["shiftAvailability"]
        if item["id"] == morning["id"]
    )
    dashboard_statuses = {
        item["key"]: item["count"]
        for item in morning_dashboard["statuses"]
    }
    assert dashboard_statuses["occupied"] == availability["allotted"]
    assert dashboard_statuses["available"] == availability["available"]
    assert dashboard_statuses["maintenance"] == availability["maintenance"]
    assert (
        dashboard_statuses["blocked"]
        == availability["blocked"] + availability["physicallyBlocked"]
    )

    reports_response = client.get(
        "/api/v1/reports",
        params={
            "startMonth": month,
            "endMonth": month,
        },
        headers=owner_headers,
    )
    assert reports_response.status_code == 200
    reports = reports_response.json()["data"]
    assert reports["revenue"]["totals"]["expected"] == "2000.00"
    assert reports["revenue"]["totals"]["collected"] == "1300.00"
    assert reports["revenue"]["totals"]["pending"] == "700.00"
    assert (
        reports["revenue"]["totals"]["collected"]
        == payments["summary"]["totalCollectedAmount"]
    )
    assert reports["pendingPayments"]["totals"]["pendingCount"] == 1
    assert reports["pendingPayments"]["totals"]["pendingAmount"] == "700.00"
    shift_reports = client.get(
        "/api/v1/reports",
        params={
            "startMonth": month,
            "endMonth": month,
            "shiftId": morning["id"],
        },
        headers=owner_headers,
    ).json()["data"]
    assert (
        shift_reports["occupancy"]["byShift"][0]["occupied"]
        == availability["allotted"]
    )
    assert (
        shift_reports["occupancy"]["byShift"][0]["available"]
        == availability["available"]
    )
    floor_reports = client.get(
        "/api/v1/reports",
        params={
            "startMonth": month,
            "endMonth": month,
            "floorId": floors[0]["id"],
        },
        headers=owner_headers,
    ).json()["data"]
    assert floor_reports["occupancy"]["totals"]["totalSeats"] == len(seats)
    assert len(floor_reports["occupancy"]["byFloor"]) == 1
    assert floor_reports["occupancy"]["byFloor"][0]["floor"] == floors[0]["id"]


def test_report_options_validation_tenant_isolation_and_permissions(
    api,
    owner_headers,
) -> None:
    client, _ = api
    options_response = client.get(
        "/api/v1/reports/options",
        headers=owner_headers,
    )
    assert options_response.status_code == 200
    options = options_response.json()["data"]
    assert options["months"]
    assert options["floors"]
    assert options["shifts"]

    invalid = client.get(
        "/api/v1/reports",
        params={"startMonth": "2026-08", "endMonth": "2026-07"},
        headers=owner_headers,
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "REPORT_INVALID_MONTH_RANGE"
    assert invalid.headers["x-request-id"]

    second_registration = register(
        client,
        libraryName="Other Report Library",
        email="other.report.owner@example.com",
        phone="9876543298",
    )
    second_headers = bearer(second_registration.json()["accessToken"])
    other_options = client.get(
        "/api/v1/reports/options",
        headers=second_headers,
    ).json()["data"]
    hidden_floor = client.get(
        "/api/v1/reports",
        params={"floorId": other_options["floors"][0]["value"]},
        headers=owner_headers,
    )
    hidden_shift = client.get(
        "/api/v1/reports",
        params={"shiftId": other_options["shifts"][0]["value"]},
        headers=owner_headers,
    )
    assert hidden_floor.status_code == hidden_shift.status_code == 404
    assert hidden_floor.json()["error"]["code"] == "REPORT_FLOOR_NOT_FOUND"
    assert hidden_shift.json()["error"]["code"] == "REPORT_SHIFT_NOT_FOUND"

    empty_dashboard = client.get(
        "/api/v1/reports/dashboard",
        headers=second_headers,
    )
    assert empty_dashboard.status_code == 200
    empty_data = empty_dashboard.json()["data"]
    assert empty_data["metrics"]["totalStudents"] == 0
    assert empty_data["metrics"]["collectedAmount"] == "0.00"
    assert empty_data["metrics"]["pendingAmount"] == "0.00"
    assert empty_data["recentActivity"] == []

    assert client.get("/api/v1/reports").status_code == 401

    invited = client.post(
        "/api/v1/students",
        json=student_payload(
            email="report.student@example.com",
            phone="9876543277",
            joiningDate=date.today().isoformat(),
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
    login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": invited["email"],
            "password": "StudentPass123",
        },
    )
    assert login.status_code == 200
    student_headers = bearer(login.json()["accessToken"])
    assert client.get(
        "/api/v1/reports/dashboard",
        headers=student_headers,
    ).status_code == 403
