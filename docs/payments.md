# Payments and Monthly Fees

## Scope

Phase 3 implements owner/staff monthly fee generation, tenant-scoped payment
lists, and append-only full or partial payment transactions. Receipts,
reminders, refunds, scheduled generation, and student self-service payment APIs
remain outside this phase.

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
  writes the audit event, and commits once. This boundary leaves receipt
  creation available for a later phase without changing payment semantics.

## API Mapping

| Frontend operation | API |
| --- | --- |
| Load/filter/page monthly records | `GET /api/v1/payments` |
| Load payment history | `GET /api/v1/payments` |
| Generate selected month | `POST /api/v1/payments/monthly-generation` |
| Record full or partial payment | `POST /api/v1/payments/{feeRecordId}/transactions` |

The Vue page calls the Pinia payment store, which calls
`frontend/src/services/paymentService.js`, which uses the shared Axios client.
The page never calculates authoritative payment status and has no mock fallback.
The unfinished receipt mock is isolated in `receiptMockService.js` and is not
used by the monthly-fee workflow.

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

Validation errors, including invalid months, zero/negative amounts, excessive
decimal precision, and unsupported payment methods, use `VALIDATION_ERROR`.
All error responses include the request ID.

## Verification

From the repository root:

```bash
backend/venv/bin/pytest backend/tests/test_payment_api.py -q
backend/venv/bin/pytest backend/tests/test_payment_concurrency_postgres.py -q
backend/venv/bin/python backend/scripts/export_openapi.py --check
backend/venv/bin/pytest backend/tests/test_openapi_contract.py -q
```

The PostgreSQL lock test requires `TEST_POSTGRES_DATABASE_URL`.

From `frontend/`:

```bash
npm test
npm run lint
npm run build
```
