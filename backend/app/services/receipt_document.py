"""Deterministic PDF rendering for immutable receipt snapshots."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from app.schemas.receipt import ReceiptDetail


def document_rows(receipt: ReceiptDetail) -> list[tuple[str, str]]:
    actor = receipt.payment.recorded_by
    return [
        ("Receipt number", receipt.receipt_number),
        ("Status", receipt.status.value.title()),
        ("Issue date", receipt.issued_at.isoformat()),
        ("Student", receipt.student.name),
        ("Enrollment number", receipt.student.enrollment_number),
        ("Billing month", receipt.fee.billing_month),
        ("Payment amount", f"{receipt.currency} {receipt.payment.amount:.2f}"),
        ("Payment method", receipt.payment.method.value.replace("_", " ").title()),
        ("Payment reference", receipt.payment.reference_number or "Not provided"),
        ("Payment date", receipt.payment.paid_at.isoformat()),
        ("Fee total", f"{receipt.currency} {receipt.fee.total_amount:.2f}"),
        (
            "Previously paid",
            f"{receipt.currency} {receipt.fee.previously_paid_amount:.2f}",
        ),
        (
            "Remaining balance",
            f"{receipt.currency} {receipt.fee.remaining_balance:.2f}",
        ),
        ("Payment status", receipt.fee.payment_status.value.replace("_", " ").title()),
        ("Recorded by", actor.name if actor else "System"),
        ("Notes", receipt.payment.notes or "None"),
    ]


def render_receipt_pdf(receipt: ReceiptDetail) -> bytes:
    buffer = BytesIO()
    pdf = Canvas(
        buffer,
        pagesize=A4,
        pageCompression=0,
        invariant=1,
    )
    width, height = A4
    y = height - 56
    pdf.setTitle(f"Receipt {receipt.receipt_number}")
    pdf.setAuthor(receipt.library.name)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, y, receipt.library.name[:72])
    y -= 22
    pdf.setFont("Helvetica", 9)
    for line in [
        receipt.library.address,
        " | ".join(
            value
            for value in [receipt.library.phone, receipt.library.email]
            if value
        ),
    ]:
        if line:
            pdf.drawString(48, y, line[:105])
            y -= 14

    y -= 12
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(48, y, "Payment Receipt")
    y -= 26
    for label, value in document_rows(receipt):
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(48, y, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(190, y, str(value)[:80])
        y -= 18
        if y < 70:
            pdf.showPage()
            y = height - 56

    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(
        48,
        42,
        "This is a system-generated receipt and does not require a signature.",
    )
    pdf.save()
    return buffer.getvalue()
