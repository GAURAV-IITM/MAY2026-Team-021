# Owner Dashboard and Reports

## Scope and Source of Truth

The Owner dashboard and reports are read-only projections over existing tenant
data. They never persist counters and never use frontend mock records. Every
query derives `library_id` from the active Library Owner or staff membership.

Money uses `Decimal` values from fee records and completed payment
transactions. Dates are interpreted in the library timezone. API month filters
use `YYYY-MM` and include both boundary months.

## Metric Definitions

| Metric | Meaning and formula | Source and inclusion rules | Reconciliation |
| --- | --- | --- | --- |
| Total students | Count of library students | `students`; excludes `deleted_at` records; all lifecycle statuses | Unfiltered student-list total |
| Active students | Count with status `active` | `students.status`; excludes soft-deleted records | Student list filtered to `active` |
| New students | Students whose business joining date is in the selected months | `students.joined_on`; excludes soft-deleted records | Student-list joining dates |
| Seat total | Active physical seats in scope | `seats`; excludes deleted or inactive seats; optional floor filter | Physical seat list |
| Occupied seats | Distinct scoped seats with an active allocation on the report date; when a shift is selected, the allocation shift snapshot must overlap its time | `seat_allocations`; status `active`; inclusive `start_date <= date <= end_date`; authoritative overnight-aware overlap utility | Seat-availability endpoint for the same date and shift |
| Available seats | Operationally available scoped seats not occupied or overlap-blocked in the selected time window | `seats.operational_status` plus active allocations | Seat-availability endpoint |
| Maintenance seats | Active seats whose physical status is `maintenance` | `seats.operational_status` | Physical seat list |
| Physically blocked seats | Active seats whose physical status is `blocked` | `seats.operational_status` | Physical seat list |
| Allocation-blocked seats | Seats unavailable because an allocation in another shift overlaps the selected shift | Allocation shift snapshots and overnight-aware time overlap | Seat-availability endpoint |
| Occupancy rate | `occupied / allocatable * 100` | Allocatable denominator excludes maintenance and physically blocked seats | Occupancy counts above |
| Billed amount | Sum of fee totals for included billing months | `fee_records.total_amount`; excludes `waived` and `cancelled` records | Payment-list summary for the same billing scope |
| Collected amount | Sum of completed transactions attached to included fee records | `payment_transactions.amount`; status `completed`; grouped by fee billing month, not payment date | Completed transaction sum |
| Outstanding amount | `max(fee total - completed transaction sum, 0)` per fee, then summed | Same fee scope; waived/cancelled excluded | Payment-list calculated balances |
| Collection rate | `collected / billed * 100`; zero when billed is zero | Revenue values above | Revenue summary |
| Pending fees | Fee records with calculated balance greater than zero | Status fields are descriptive only; completed transactions determine balance | Payment-list balances |
| Overdue amount | Positive balances whose `due_date` is before the report date | Fee records and completed transactions | Pending-fee detail rows |
| Ageing | Not due, 1-30, 31-60, 61-90, or 90+ days overdue | `report_date - due_date`; due today is not overdue | Pending-fee rows |
| Shift occupancy | Distinct seats occupied by allocations whose stored shift times overlap the displayed shift | Active allocations on report date; maintenance and physical blocking remain separate | Seat map for the same shift/date |
| Student shift distribution | Distinct students with an active allocation in each displayed shift on the report date | Active allocation rows; one student counted once per shift | Allocation list |
| Recent activity | Latest real administrative audit events | `audit_logs`; tenant-scoped; limited to 6; safe descriptions only | Audit table |
| Attention items | Highest-priority actionable condition per student | Inactive student with active allocation, overdue fee, pending seat request, missing active allocation, then allocation expiring within 7 days | Source module lists |

## Date Semantics

- Dashboard `date` defaults to the current date in the library timezone.
- Dashboard `billingMonth` defaults to the dashboard date's month.
- Reports default to the latest three months in the options window.
- Report occupancy is a selected-date snapshot. The date is the earlier of the
  report end month's final day and the current library-local date.
- Revenue is grouped by fee `billing_month`. A later payment against an older
  fee is reported with that fee's billing month.
- Student growth uses `joined_on`, not record creation time.

## Filters

`floorId` and `shiftId` are tenant-scoped identifiers. Missing, deleted, or
cross-tenant values return the established not-found response. Inactive shifts
remain available in report options only when historical allocations reference
them; deleted shifts are excluded.

The options endpoint returns a rolling 12-month window ending in the current
library month, unioned with months represented by fee, payment, and student
records.

## Frontend Mapping

- `dashboardService` calls `GET /api/v1/reports/dashboard`.
- `analyticsService` calls `GET /api/v1/reports/options` and
  `GET /api/v1/reports`.
- Chart.js renders API series without recalculating authoritative totals.
- CSV export uses only the currently loaded authorised response and escapes
  commas, quotes, and newlines.
- Print uses the loaded report, library name, filters, and generation time; it
  does not issue another request.

## Audit Coverage

Recent activity can currently include payments, receipts, reminders,
allocations, seat-request reviews, announcements, and monthly fee generation.
Student CRUD does not yet write audit events, so no synthetic registration
activity is generated.

## Performance Policy

Reports use separate tenant-scoped queries for students, seats, allocations,
fees, transactions, and audit records to avoid multiplying financial sums.
Recent activity is limited to 6 records, attention is limited to 6 students,
and pending-fee detail is capped at 200 rows while totals and ageing continue
to cover the complete selected scope. Existing indexes cover
library/month fees, library/payment date, allocation conflict date lookups,
seat floor/status, and audit library/date. New indexes are added only after a
PostgreSQL query plan demonstrates a need.

## Verification

```bash
backend/venv/bin/python -m pytest backend/tests -q
backend/venv/bin/python backend/scripts/export_openapi.py --check
cd frontend && npm test
cd frontend && npm run lint
cd frontend && npm run build
```
