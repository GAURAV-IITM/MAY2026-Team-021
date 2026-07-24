# Database Rules and Service Invariants

Some rules can be expressed directly by constraints. Others require a service
transaction because they depend on several rows and time intervals.

## Tenant isolation

- Every library-owned row has a non-null `library_id`.
- Repositories must require `library_id` for tenant queries.
- Services must verify that referenced students, seats, floors, shifts, fee
  records, and announcements belong to that same library.
- The authenticated user's active `library_memberships` row determines the
  tenant. A client-supplied library ID is never trusted by itself.
- Super-admin operations are separate, explicitly authorized routes.

## Seats and shifts

- `seats.operational_status` stores only `available`, `maintenance`, or
  `blocked`. Occupancy is not a permanent seat property.
- A maintenance or blocked seat cannot receive a new allocation.
- Inactive or soft-deleted seats and shifts remain readable through history but
  cannot be used for new allocations.
- A shift may cross midnight. `22:00-02:00` overlaps `01:00-06:00`.
- Shift selection for one student must reject any pair whose daily time windows
  overlap. Adjacent windows such as `06:00-12:00` and `12:00-18:00` are valid.

For comparison, split a shift that crosses midnight into two half-open ranges:

```text
22:00-02:00 -> [22:00, 24:00) and [00:00, 02:00)
01:00-06:00 -> [01:00, 06:00)
```

Two shifts overlap if any normalized ranges intersect.

## Seat allocations

- `end_date` must be on or after `start_date`.
- Active allocations block only when both their inclusive date ranges and their
  daily shift windows overlap.
- The same seat cannot be allocated to two students during an overlapping
  period and time window.
- The same student cannot hold two seats during an overlapping period and time
  window.
- Different non-overlapping shifts may use the same seat on the same dates.
- A later allocation is valid only when its start date is after the previous
  allocation's inclusive end date.
- Completed and cancelled allocations do not block new bookings.
- Allocation conflicts must be checked while holding transaction locks on the
  affected seat and student before inserting. The supporting conflict indexes
  are defined on `seat_allocations`.
- A transfer closes the current allocation and inserts a new allocation with
  `previous_allocation_id` and a shared `transfer_group_id` in one transaction.
- Shift name and time snapshots preserve historical meaning if a shift changes.

Seat-map status for a selected date range and shift is derived in this order:

1. `Maintenance` when the seat's physical state is maintenance.
2. `Blocked` when the physical state is blocked.
3. `Allotted` when an active allocation uses the selected shift and dates.
4. `Blocked` when another active allocation's shift overlaps the selected time.
5. `Reserved` when the matching allocation begins in the future.
6. `Available` when none of the above applies.

## Status and deletion history

- Seat status changes append a `seat_status_events` row, including who changed
  it, why, and the effective period.
- Users, libraries, students, floors, shifts, seats, and announcements use soft
  deletion where history matters.
- Allocations, fee records, payment transactions, receipts, reminders, and
  audit logs must not be hard-deleted through normal application workflows.
- Administrative create, update, status, transfer, cancellation, and deletion
  requests append an `audit_logs` row with actor and before/after values.

## Student access

- Only active students may receive new allocations.
- A student portal account is linked through `students.user_id`.
- New students should receive an expiring password-setup invitation. Plain-text
  passwords must never be stored, logged, or sent by the API.
- Student portal queries derive `student_id` from the authenticated user rather
  than accepting another student's ID from the browser.

## Fees and receipts

- There is at most one fee record per library, student, and billing month.
- Monthly generation is idempotent and targets eligible active students.
- A fee record may have multiple transactions, which supports partial payment.
- Fee status is updated transactionally from completed transaction totals.
- Each completed transaction may produce one receipt. Receipt snapshots retain
  the original student, library, amount, method, and billing details.
- Receipt numbers are unique within a library.
- WhatsApp, SMS, and email attempts are recorded in `payment_reminders`.

## Announcements and reports

- Draft, scheduled, published, expired, and archived announcements remain in
  one lifecycle table.
- Student read state is unique per announcement and student.
- Dashboard and report values are computed from source records and date filters.
  Cached or materialized aggregates should only be introduced after profiling.
