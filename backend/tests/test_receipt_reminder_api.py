"""Receipt access, atomicity, and WhatsApp reminder API coverage."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import func, select

from app.models.audit import AuditLog
from app.models.enums import DeliveryStatus, FeeStatus
from app.models.library import Library, LibrarySettings
from app.models.payment import FeeRecord, PaymentReminder, PaymentTransaction, Receipt
from app.models.student import Student
from app.services import receipt as receipt_service
from tests.api_helpers import bearer, register
from tests.test_core_library_api import student_payload


MONTH = "2026-07"


def _create_fee(client, headers, *, phone="+91 99999 99999", fee_amount=1000):
    student_response = client.post(
        "/api/v1/students",
        json=student_payload(
            sendInvitation=False,
            phone=phone,
            feeAmount=fee_amount,
        ),
        headers=headers,
    )
    assert student_response.status_code == 201
    generated = client.post(
        "/api/v1/payments/monthly-generation",
        json={"month": MONTH},
        headers=headers,
    )
    assert generated.status_code == 201
    return generated.json()["data"]["createdPayments"][0]


def _record(client, headers, fee_id, amount, reference):
    return client.post(
        f"/api/v1/payments/{fee_id}/transactions",
        json={
            "amount": amount,
            "method": "upi",
            "referenceNumber": reference,
        },
        headers=headers,
    )


def test_payments_create_snapshot_receipts_and_secure_receipt_access(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    fee = _create_fee(client, owner_headers)

    partial = _record(
        client,
        owner_headers,
        fee["id"],
        "400.00",
        "UPI-RECEIPT-PARTIAL",
    )
    assert partial.status_code == 201
    first_receipt = partial.json()["data"]["receipt"]
    assert first_receipt["amount"] == "400.00"
    assert first_receipt["billingMonth"] == MONTH
    assert first_receipt["status"] == "issued"

    final = _record(
        client,
        owner_headers,
        fee["id"],
        "600.00",
        "UPI-RECEIPT-FINAL",
    )
    assert final.status_code == 201
    second_receipt = final.json()["data"]["receipt"]
    assert second_receipt["amount"] == "600.00"
    assert second_receipt["id"] != first_receipt["id"]

    listed = client.get(
        "/api/v1/payments/receipts",
        params={
            "billingMonth": MONTH,
            "paymentMethod": "upi",
            "search": "UPI-RECEIPT-PARTIAL",
            "sortBy": "paidAt",
            "sortOrder": "asc",
        },
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["meta"]["totalItems"] == 1
    assert listed.json()["data"][0]["id"] == first_receipt["id"]

    detail = client.get(
        f"/api/v1/payments/receipts/{first_receipt['id']}",
        headers=owner_headers,
    )
    assert detail.status_code == 200
    snapshot = detail.json()["data"]
    assert snapshot["fee"]["previouslyPaidAmount"] == "0.00"
    assert snapshot["fee"]["remainingBalance"] == "600.00"
    assert snapshot["payment"]["amount"] == "400.00"

    with testing_session() as db:
        student = db.scalar(select(Student))
        library = db.scalar(select(Library))
        student.first_name = "Changed"
        student.deleted_at = datetime.now(timezone.utc)
        library.name = "Changed Library"
        db.commit()

    unchanged = client.get(
        f"/api/v1/payments/receipts/{first_receipt['id']}",
        headers=owner_headers,
    ).json()["data"]
    assert unchanged["student"]["name"] != "Changed Sharma"
    assert unchanged["library"]["name"] != "Changed Library"

    downloaded = client.get(
        f"/api/v1/payments/receipts/{first_receipt['id']}/download",
        headers=owner_headers,
    )
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/pdf"
    assert first_receipt["receiptNumber"] in downloaded.headers[
        "content-disposition"
    ]
    assert downloaded.body.startswith(b"%PDF")

    with testing_session() as db:
        stored_receipt = db.scalar(
            select(Receipt).where(
                Receipt.id == uuid.UUID(first_receipt["id"])
            )
        )
        transaction = db.get(
            PaymentTransaction,
            stored_receipt.transaction_id,
        )
        stored_fee = db.get(FeeRecord, transaction.fee_record_id)
        reused = receipt_service.issue_receipt(
            db,
            library_id=stored_receipt.library_id,
            fee=stored_fee,
            transaction=transaction,
            paid_before=0,
            paid_after=transaction.amount,
            actor_user_id=transaction.recorded_by_user_id,
        )
        assert reused.id == stored_receipt.id
        assert db.scalar(select(func.count(Receipt.id))) == 2
        assert db.scalar(select(func.count(PaymentTransaction.id))) == 2
        assert (
            db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action == "receipt.issued"
                )
            )
            == 2
        )

    other = register(
        client,
        libraryName="Hidden Receipt Library",
        email="hidden.receipt.owner@example.com",
        phone="9876543201",
    )
    other_headers = bearer(other.json()["accessToken"])
    assert client.get(
        f"/api/v1/payments/receipts/{first_receipt['id']}",
        headers=other_headers,
    ).status_code == 404
    assert client.get(
        f"/api/v1/payments/receipts/{first_receipt['id']}/download",
        headers=other_headers,
    ).status_code == 404


def test_receipt_failure_rolls_back_all_financial_state(
    api,
    owner_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, testing_session = api
    fee = _create_fee(client, owner_headers)

    def fail_receipt(*_args, **_kwargs):
        raise RuntimeError("forced receipt failure")

    monkeypatch.setattr(receipt_service, "issue_receipt", fail_receipt)
    with pytest.raises(RuntimeError, match="forced receipt failure"):
        _record(
            client,
            owner_headers,
            fee["id"],
            "500.00",
            "ROLLBACK-RECEIPT",
        )

    with testing_session() as db:
        stored_fee = db.get(FeeRecord, uuid.UUID(fee["id"]))
        assert stored_fee.status == FeeStatus.UNPAID
        assert db.scalar(select(func.count(PaymentTransaction.id))) == 0
        assert db.scalar(select(func.count(Receipt.id))) == 0
        assert (
            db.scalar(
                select(func.count(AuditLog.id)).where(
                    AuditLog.action.in_(
                        [
                            "payment_transaction.recorded",
                            "receipt.issued",
                        ]
                    )
                )
            )
            == 0
        )


def test_whatsapp_reminder_persists_link_generation_without_delivery_claim(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    fee = _create_fee(client, owner_headers)
    partial = _record(
        client,
        owner_headers,
        fee["id"],
        "400.00",
        "UPI-REMINDER-PARTIAL",
    )
    assert partial.status_code == 201

    other = register(
        client,
        libraryName="Other Reminder Library",
        email="other.reminder.owner@example.com",
        phone="9876543202",
    )
    cross_tenant = client.post(
        f"/api/v1/payments/{fee['id']}/reminders",
        json={"channel": "whatsapp"},
        headers=bearer(other.json()["accessToken"]),
    )
    assert cross_tenant.status_code == 404
    assert cross_tenant.json()["error"]["code"] == "PAYMENT_NOT_FOUND"

    response = client.post(
        f"/api/v1/payments/{fee['id']}/reminders",
        json={"channel": "whatsapp"},
        headers={**owner_headers, "X-Request-ID": "reminder-link-test"},
    )
    assert response.status_code == 201
    assert response.headers["x-request-id"] == "reminder-link-test"
    result = response.json()["data"]
    assert result["reminder"]["outcome"] == "link_generated"
    assert result["whatsappUrl"].startswith(
        "https://wa.me/919999999999?text="
    )
    message = parse_qs(urlsplit(result["whatsappUrl"]).query)["text"][0]
    assert "INR 600.00" in message
    assert "July 2026" in message

    with testing_session() as db:
        reminder = db.scalar(select(PaymentReminder))
        assert reminder.status == DeliveryStatus.QUEUED
        assert reminder.sent_at is None
        assert reminder.recipient == "919999999999"
        audit = db.scalar(
            select(AuditLog).where(
                AuditLog.action == "payment_reminder.link_generated"
            )
        )
        assert audit is not None
        assert audit.new_values["outcome"] == "link_generated"

    completed = _record(
        client,
        owner_headers,
        fee["id"],
        "600.00",
        "UPI-REMINDER-FINAL",
    )
    assert completed.status_code == 201
    paid = client.post(
        f"/api/v1/payments/{fee['id']}/reminders",
        json={"channel": "whatsapp"},
        headers=owner_headers,
    )
    assert paid.status_code == 409
    assert paid.json()["error"]["code"] == "REMINDER_PAYMENT_CLOSED"


def test_reminder_defaults_local_phone_to_india_and_honours_disabled_setting(
    api,
    owner_headers,
) -> None:
    client, testing_session = api
    fee = _create_fee(client, owner_headers, phone="9876543210")
    generated = client.post(
        f"/api/v1/payments/{fee['id']}/reminders",
        json={"channel": "whatsapp"},
        headers=owner_headers,
    )
    assert generated.status_code == 201
    assert generated.json()["data"]["whatsappUrl"].startswith(
        "https://wa.me/919876543210?text="
    )

    with testing_session() as db:
        settings = db.scalar(select(LibrarySettings))
        settings.whatsapp_reminders_enabled = False
        db.commit()

    disabled = client.post(
        f"/api/v1/payments/{fee['id']}/reminders",
        json={"channel": "whatsapp"},
        headers=owner_headers,
    )
    assert disabled.status_code == 409
    assert (
        disabled.json()["error"]["code"]
        == "WHATSAPP_REMINDERS_DISABLED"
    )
    with testing_session() as db:
        assert db.scalar(select(func.count(PaymentReminder.id))) == 1
