"""Monthly fee generation and payment transaction API coverage."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import func, select

from app.models.audit import AuditLog
from app.models.enums import FeeStatus, PaymentTransactionStatus
from app.models.library import LibrarySettings
from app.models.payment import FeeRecord, PaymentTransaction
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


MONTH = "2026-07"


def _create_student(client, headers, **overrides):
    response = client.post(
        "/api/v1/students",
        json=student_payload(sendInvitation=False, **overrides),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


def _generate(client, headers, month=MONTH):
    return client.post(
        "/api/v1/payments/monthly-generation",
        json={"month": month},
        headers=headers,
    )


def test_monthly_generation_is_server_derived_idempotent_and_filtered(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    first = _create_student(client, owner_headers)
    second = _create_student(
        client,
        owner_headers,
        firstName="Ananya",
        lastName="Das",
        email="ananya.payments@example.com",
        phone="9876543212",
        feeAmount=875.50,
    )
    _create_student(
        client,
        owner_headers,
        firstName="Inactive",
        lastName="Student",
        email="inactive.payments@example.com",
        phone="9876543213",
        status="inactive",
    )

    generated = _generate(client, owner_headers)
    assert generated.status_code == 201
    result = generated.json()["data"]
    assert result["activeStudentCount"] == 2
    assert result["eligibleStudentCount"] == 2
    assert result["createdCount"] == 2
    assert result["existingCount"] == 0
    assert result["skippedCount"] == 1
    assert result["skippedStudents"][0]["reason"] == "student_not_active"
    assert {
        payment["student"]["id"]
        for payment in result["createdPayments"]
    } == {first["id"], second["id"]}

    repeated = _generate(client, owner_headers)
    assert repeated.status_code == 201
    assert repeated.json()["data"]["createdCount"] == 0
    assert repeated.json()["data"]["existingCount"] == 2

    listed = client.get(
        "/api/v1/payments",
        params={
            "month": MONTH,
            "page": 1,
            "pageSize": 1,
            "search": "Ananya",
        },
        headers=owner_headers,
    )
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["meta"] == {
        "page": 1,
        "pageSize": 1,
        "totalItems": 1,
        "totalPages": 1,
    }
    assert payload["data"][0]["student"]["id"] == second["id"]
    assert payload["data"][0]["totalAmount"] == "875.50"
    assert payload["data"][0]["paidAmount"] == "0.00"
    assert payload["data"][0]["balanceAmount"] == "875.50"
    assert payload["summary"]["unpaidCount"] == 1
    assert payload["summary"]["totalPendingAmount"] == "875.50"
    history = client.get(
        "/api/v1/payments",
        params={"month": MONTH, "hasTransactions": True},
        headers=owner_headers,
    )
    assert history.status_code == 200
    assert history.json()["meta"]["totalItems"] == 0

    with testing_session() as db:
        assert (
            db.scalar(select(func.count(FeeRecord.id)))
            == 2
        )
        audit = db.scalar(
            select(AuditLog)
            .where(AuditLog.action == "monthly_fees.generated")
            .order_by(AuditLog.created_at.asc())
        )
        assert audit is not None
        assert audit.new_values["createdCount"] == 2


def test_partial_and_full_payments_recalculate_server_totals(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    _create_student(client, owner_headers, feeAmount=1200)
    fee = _generate(client, owner_headers).json()["data"][
        "createdPayments"
    ][0]

    partial = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={
            "amount": "400.25",
            "method": "upi",
            "referenceNumber": "UPI-PARTIAL-001",
            "notes": "First instalment",
        },
        headers={**owner_headers, "X-Request-ID": "payment-partial-test"},
    )
    assert partial.status_code == 201
    assert partial.headers["x-request-id"] == "payment-partial-test"
    payment = partial.json()["data"]["payment"]
    assert payment["paidAmount"] == "400.25"
    assert payment["balanceAmount"] == "799.75"
    assert payment["status"] == "partially_paid"
    assert payment["latestTransaction"]["recordedBy"]["name"]

    overpayment = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={"amount": "800.00", "method": "cash"},
        headers=owner_headers,
    )
    assert overpayment.status_code == 422
    assert (
        overpayment.json()["error"]["code"]
        == "PAYMENT_AMOUNT_EXCEEDS_BALANCE"
    )
    assert overpayment.json()["error"]["details"] == {
        "remainingBalance": "799.75",
        "submittedAmount": "800.00",
    }

    completed = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={
            "amount": "799.75",
            "method": "cash",
            "referenceNumber": "CASH-FINAL-001",
        },
        headers=owner_headers,
    )
    assert completed.status_code == 201
    paid = completed.json()["data"]["payment"]
    assert paid["paidAmount"] == "1200.00"
    assert paid["balanceAmount"] == "0.00"
    assert paid["status"] == "paid"
    assert len(paid["transactions"]) == 2

    closed = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={"amount": "1.00", "method": "cash"},
        headers=owner_headers,
    )
    assert closed.status_code == 409
    assert closed.json()["error"]["code"] == "PAYMENT_ALREADY_PAID"

    listed = client.get(
        "/api/v1/payments",
        params={"month": MONTH, "status": "paid"},
        headers=owner_headers,
    ).json()
    assert listed["summary"]["paidCount"] == 1
    assert listed["summary"]["totalCollectedAmount"] == "1200.00"
    assert listed["summary"]["totalPendingAmount"] == "0.00"

    with testing_session() as db:
        transaction_count = db.scalar(
            select(func.count(PaymentTransaction.id)).where(
                PaymentTransaction.status
                == PaymentTransactionStatus.COMPLETED
            )
        )
        fee_status = db.scalar(select(FeeRecord.status))
        audit_count = db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.action == "payment_transaction.recorded"
            )
        )
    assert transaction_count == 2
    assert fee_status == FeeStatus.PAID
    assert audit_count == 2


def test_payment_validation_role_and_tenant_isolation(
    api,
    owner_headers,
) -> None:
    client, _ = api
    student_response = client.post(
        "/api/v1/students",
        json=student_payload(sendInvitation=True),
        headers=owner_headers,
    )
    assert student_response.status_code == 201
    student = student_response.json()["data"]
    fee = _generate(client, owner_headers).json()["data"][
        "createdPayments"
    ][0]

    future = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={
            "amount": "100.00",
            "method": "card",
            "paidAt": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(),
        },
        headers=owner_headers,
    )
    assert future.status_code == 422
    assert future.json()["error"]["code"] == "PAYMENT_DATE_IN_FUTURE"

    excessive_precision = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={"amount": "10.001", "method": "cash"},
        headers=owner_headers,
    )
    assert excessive_precision.status_code == 422
    assert excessive_precision.json()["error"]["code"] == "VALIDATION_ERROR"

    first = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={
            "amount": "100.00",
            "method": "bank_transfer",
            "referenceNumber": "BANK-DUPLICATE",
        },
        headers=owner_headers,
    )
    assert first.status_code == 201
    duplicate_reference = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={
            "amount": "100.00",
            "method": "bank_transfer",
            "referenceNumber": "BANK-DUPLICATE",
        },
        headers=owner_headers,
    )
    assert duplicate_reference.status_code == 409
    assert (
        duplicate_reference.json()["error"]["code"]
        == "PAYMENT_REFERENCE_EXISTS"
    )

    token = parse_qs(
        urlsplit(student["invitationSetupUrl"]).query
    )["token"][0]
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "StudentPass123"},
    )
    assert accepted.status_code == 200
    student_login = client.post(
        "/api/v1/auth/session/login",
        json={
            "email": student["email"],
            "password": "StudentPass123",
        },
    )
    student_headers = bearer(student_login.json()["accessToken"])
    assert client.get(
        "/api/v1/payments",
        headers=student_headers,
    ).status_code == 403

    other_registration = register(
        client,
        libraryName="Other Payment Library",
        email="other.payment.owner@example.com",
        phone="9876543299",
    )
    other_headers = bearer(other_registration.json()["accessToken"])
    hidden = client.post(
        f"/api/v1/payments/{fee['id']}/transactions",
        json={"amount": "10.00", "method": "cash"},
        headers=other_headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "PAYMENT_NOT_FOUND"


def test_generation_uses_library_fee_fallback_and_clamps_due_day(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    with testing_session() as db:
        settings = db.scalar(select(LibrarySettings))
        settings.default_monthly_fee = Decimal("950.25")
        settings.fee_due_day = 31
        db.commit()

    _create_student(
        client,
        owner_headers,
        joiningDate="2026-01-15",
        feeAmount=0,
    )
    generated = _generate(client, owner_headers, month="2026-02")
    assert generated.status_code == 201
    fee = generated.json()["data"]["createdPayments"][0]
    assert fee["baseAmount"] == "950.25"
    assert fee["totalAmount"] == "950.25"
    assert fee["dueDate"] == "2026-02-28"
