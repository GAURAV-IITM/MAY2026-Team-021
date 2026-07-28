# Payments and Monthly Fees

## Scope

Phase 3 implements owner/staff monthly fee generation, tenant-scoped payment
lists, and append-only full or partial payment transactions. Phase 4 adds
automatic receipts, tenant-scoped receipt preview/download, and auditable
WhatsApp reminder-link generation. Refunds, scheduled generation, provider
delivery tracking, and student self-service receipt APIs remain outside scope.

## Monthly Fee Generation

- Billing months use `YYYY-MM` in the API and the first day of that month in
  `fee_records.billing_month`.
- The authenticated membership supplies the library. A client cannot choose a
  library or submit student IDs or fee totals.
- Non-deleted students are inspected. Only students with `active` status who
  were enrolled during the billing month are eligible.
- A student who joins during the month receives the full monthly fee. Proration
  is not implemented because the current product model has no proration rule.
- The student `monthly_fee` is used when it is greater than zero. Otherwise,
  `library_settings.default_monthly_fee` is used. A student is skipped when
  neither value is greater than zero.
- The due date comes from `library_settings.fee_due_day` and is clamped to the
  final day of short months.
- Discounts and late fees are currently `0.00`; no discount or late-fee rule is
  represented in the current settings or student models.
- The formula is
  `total_amount = base_amount - discount_amount + late_fee_amount`, using
  `Decimal`/`NUMERIC(12,2)` values.
- Generation is all-or-none. It locks the library row, checks existing records,
  inserts the batch, writes one summary audit event, and commits once.
- `uq_fee_record_student_month` guarantees at most one record for each
  library/student/month. Repeating generation safely reports existing records.

## Payment Transactions

- The server locks the tenant-owned fee record before reading completed
  transactions and calculating its latest balance.
- `paid_amount` is the sum of completed transaction amounts.
- `balance_amount = total_amount - paid_amount`.
- Status is `unpaid` at zero paid, `partially_paid` between zero and the total,
  and `paid` at the exact total.
- A payment greater than the locked remaining balance is rejected. A failed
  payment creates no transaction, status change, or success audit event.
- Transactions are append-only and preserve amount, method, paid time,
  reference, notes, actor, and creation time. Earlier partial payments remain
  visible after the final payment.
- A reference number cannot be reused on the same fee record.
- Payment recording writes the transaction, updates the cached fee status,
  issues its receipt, writes payment and receipt audit events, and commits
  once. A receipt failure rolls back the transaction, fee status, receipt, and
  both success audit events.

## Automatic Receipts

- Every completed payment transaction receives exactly one receipt. The
  database enforces this with the unique `receipts.transaction_id` column.
- An idempotent receipt issue call first looks up the tenant-owned transaction
  receipt and reuses it when present.
- Receipt numbers use
  `{library receipt prefix}-{paid year}-{receipt UUID hex}`. This is
  human-readable, does not depend on an unsafe row count, and is protected by
  `uq_receipt_library_number`.
- Each receipt stores an immutable JSON snapshot of the library identity and
  contact details, student name and enrollment number, fee totals, billing
  month, payment facts, remaining balance, actor, notes, and `INR` currency.
  Later edits to a student or library do not rewrite receipt history.
- Receipt list, preview, and PDF all read from the stored snapshot. The PDF
  renderer does not recalculate financial values and does not mutate state.
- ReportLab renders a server-generated PDF. Downloads require the same
  authenticated tenant lookup as preview; there is no public URL or token in a
  query string.

### Receipt Ownership

| Actor | Current-library receipt | Other-library receipt |
| --- | --- | --- |
| Library owner | List, preview, download | Hidden as `404` |
| Active staff | List, preview, download | Hidden as `404` |
| Student | Deferred to Student Portal API | Not allowed |
| Unauthenticated user | `401` | `401` |

Receipt queries constrain receipt, transaction, fee record, and student by the
authenticated membership's `library_id` before serialisation. Future student
routes can derive the student through the authenticated `Student.user_id`
relationship; client-supplied student IDs must never authorise access.

## WhatsApp Payment Reminders

- `POST /payments/{feeRecordId}/reminders` supports only `whatsapp`.
- The server locks and rechecks the tenant-owned fee. Only unpaid or partially
  paid records with a positive current balance are eligible.
- Library settings must have `whatsapp_reminders_enabled=true`.
- Phone normalisation removes spaces, hyphens, parentheses, and one leading
  `+`. The result must contain 8-15 digits. India (`91`) is the application
  default country code, so a ten-digit local number such as `9876543210`
  becomes `919876543210`. An eleven-digit Indian number beginning with the
  domestic `0` prefix is normalised the same way. Numbers that already contain
  an international country code remain unchanged.
- The default message contains the student, library, billing month, current
  balance, due date, and contact guidance. “Overdue” wording is used only when
  the due date has passed.
- Links use `https://wa.me/{digits}?text={encodedMessage}`.
- A `PaymentReminder` row and audit event are committed before the URL is
  returned. The existing database `queued` state means that link generation
  was recorded but provider delivery is unknown. The API exposes the clearer
  outcome `link_generated`.
- A link being generated or opened does not prove WhatsApp opened, the
  administrator pressed Send, or the message was delivered/read. Neither API
  nor UI claims those outcomes.
- Validation failures do not create a failed attempt because no usable URL was
  generated. Legitimate repeated reminders remain separate history rows, while
  the frontend disables duplicate in-flight submission.

## API Mapping

| Frontend operation | API |
| --- | --- |
| Load/filter/page monthly records | `GET /api/v1/payments` |
| Load payment history | `GET /api/v1/payments` |
| Generate selected month | `POST /api/v1/payments/monthly-generation` |
| Record full or partial payment | `POST /api/v1/payments/{feeRecordId}/transactions` |
| Search/filter/page receipts | `GET /api/v1/payments/receipts` |
| Preview immutable receipt | `GET /api/v1/payments/receipts/{receiptId}` |
| Download authenticated PDF | `GET /api/v1/payments/receipts/{receiptId}/download` |
| Record and create WhatsApp link | `POST /api/v1/payments/{feeRecordId}/reminders` |

The Vue page calls the Pinia payment store, which calls
`frontend/src/services/paymentService.js`, which uses the shared Axios client.
The page never calculates authoritative payment status and has no mock
fallback. The admin receipt page and reminder dialog use the real API through
the same service/store boundary. Student Portal payment mocks remain separate
until student-facing APIs are implemented.

## Domain Error Codes

| Code | Meaning |
| --- | --- |
| `LIBRARY_FEE_SETTINGS_REQUIRED` | Fee generation requires library settings. |
| `MONTHLY_FEE_GENERATION_CONFLICT` | Concurrent generation conflicted; refresh safely. |
| `PAYMENT_NOT_FOUND` | The fee is missing or belongs to another library. |
| `PAYMENT_ALREADY_PAID` | The fee has no remaining balance. |
| `PAYMENT_RECORD_CLOSED` | The fee is waived or cancelled. |
| `PAYMENT_AMOUNT_EXCEEDS_BALANCE` | The submitted amount exceeds the locked balance. |
| `PAYMENT_REFERENCE_EXISTS` | The same reference already exists on the fee. |
| `PAYMENT_DATE_IN_FUTURE` | The payment timestamp is in the future. |
| `PAYMENT_DUE_DATE_RANGE_INVALID` | The list due-date range is reversed. |
| `RECEIPT_NOT_FOUND` | The receipt is missing or belongs to another library. |
| `RECEIPT_DATE_RANGE_INVALID` | The receipt issue-date range is reversed. |
| `RECEIPT_TRANSACTION_NOT_COMPLETED` | A non-completed transaction cannot receive a receipt. |
| `REMINDER_PAYMENT_CLOSED` | The fee is paid, waived, or cancelled. |
| `REMINDER_PAYMENT_ALREADY_PAID` | The recalculated balance is zero. |
| `WHATSAPP_REMINDERS_DISABLED` | The library disabled WhatsApp reminders. |
| `REMINDER_PHONE_MISSING` | The student has no phone number. |
| `REMINDER_PHONE_INVALID` | The stored phone cannot form an international `wa.me` number. |
| `REMINDER_COUNTRY_CODE_REQUIRED` | The stored number is too short for the India-default normalisation rule. |

Validation errors, including invalid months, zero/negative amounts, excessive
decimal precision, and unsupported payment methods, use `VALIDATION_ERROR`.
All error responses include the request ID.

## Verification

From the repository root:

```bash
backend/venv/bin/pytest backend/tests/test_payment_api.py -q
backend/venv/bin/pytest backend/tests/test_receipt_reminder_api.py -q
backend/venv/bin/pytest backend/tests/test_receipt_reminder_rules.py -q
backend/venv/bin/pytest backend/tests/test_payment_concurrency_postgres.py -q
backend/venv/bin/python backend/scripts/export_openapi.py --check
backend/venv/bin/pytest backend/tests/test_openapi_contract.py -q
```

The PostgreSQL lock test requires `TEST_POSTGRES_DATABASE_URL`. It verifies
that concurrent payment attempts preserve one successful financial update,
that each committed transaction has exactly one receipt, and that receipt
numbers remain unique.

From `frontend/`:

```bash
npm test
npm run lint
npm run build
```
