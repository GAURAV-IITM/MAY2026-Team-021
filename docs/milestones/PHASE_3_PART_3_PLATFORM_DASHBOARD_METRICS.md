# Phase 3, Part 3: Platform Dashboard Metrics

## Repository Findings

- Platform libraries use `pending`, `active`, and `suspended` statuses and are
  soft deleted through `Library.deleted_at`.
- Owner accounts are distinct `User` records with the global `library_owner`
  role. Tenant assignments are stored separately in `LibraryMembership` and
  must not multiply owner counts.
- `User.is_active` is the account lifecycle flag used by owner suspension.
- Students have `active`, `inactive`, `left`, and `suspended` statuses and a
  soft-delete timestamp. `joined_on` is the business date for student growth.
- Physical seats are soft deletable. Current occupancy comes from dated
  `SeatAllocation` rows and may contain several shifts for one physical seat.
- Platform administration writes append-only `AuditLog` records whose actions
  begin with `platform.`. Tenant audit events share the table.
- The current Super Admin dashboard contains four metric cards, cumulative
  student growth, library-status distribution, five top libraries, three
  attention counters, and six recent activity rows.
- Revenue, payment, subscription, and forecasting metrics are not represented
  on this screen and are outside this phase.

## Time And Range Policy

Platform trend grouping uses UTC. With no range, the endpoint returns seven
calendar months ending in the current UTC month. `startMonth` and `endMonth`
may select an inclusive range of at most 24 months; both must be supplied,
must use `YYYY-MM`, must be ordered, and may not end in the future.

All trend series are cumulative month-end totals because the current chart is
labelled as platform growth. A month without a source event carries the prior
cumulative value. Months before the first source event return zero.

## Metric Definitions

| Metric | Definition | Source and date | Exclusions | Empty value |
| --- | --- | --- | --- | --- |
| Total libraries | Distinct platform library records | `Library.id`; `created_at` for trends | Soft-deleted libraries | `0` |
| Active libraries | Distinct libraries whose status is `active` | `Library.status` | Soft-deleted libraries | `0` |
| Pending libraries | Distinct libraries whose status is `pending` | `Library.status` | Soft-deleted libraries | `0` |
| Suspended libraries | Distinct libraries whose status is `suspended` | `Library.status` | Soft-deleted libraries | `0` |
| Total owners | Distinct accepted owner user accounts with the global `library_owner` role | `User.id`; `UserRole.assigned_at` for trends | Soft-deleted users; pending invitations; duplicate memberships | `0` |
| Active owners | Total-owner accounts where `User.is_active` is true | `User.is_active` | Soft-deleted users | `0` |
| Suspended owners | Total-owner accounts where `User.is_active` is false | `User.is_active` | Soft-deleted users | `0` |
| Invited owners | Current unexpired pending owner invitations | `AccountInvitation.expires_at` and status | Accepted, expired, revoked, or already elapsed invitations | `0` |
| Total students | Distinct non-deleted student records under non-deleted libraries, including active, inactive, left, and suspended students | `Student.id`; `joined_on` for trends | Soft-deleted students or parent libraries | `0` |
| Total seats | Distinct non-deleted physical seats under non-deleted libraries | `Seat.id` | Soft-deleted seats or parent libraries | `0` |
| Platform occupancy | Weighted current utilization of physical seats in active libraries: distinct occupied seat IDs divided by non-deleted seat IDs | Active allocations where `start_date <= today <= end_date` | Duplicate shifts on one seat, inactive allocations, deleted seats/libraries, non-active libraries | `0%` |

## Bounded Summaries

### Library Status Distribution

Returns `pending`, `active`, and `suspended` with authoritative counts. All
three statuses are returned even when zero and reconcile to total libraries.

### Platform Growth

Each month contains cumulative counts for:

- Non-deleted libraries created on or before month end.
- Non-deleted students whose `joined_on` is on or before month end.
- Distinct non-deleted owner users whose global Owner role was assigned on or
  before month end.

The dashboard currently visualizes the student value; the same bounded points
also keep library and owner growth consistent for later presentation changes.

### Top Libraries

Returns at most five active, non-deleted libraries ordered by non-deleted
student count, then name. Each row includes non-deleted student count,
non-deleted physical seat count, and current distinct-seat occupancy percentage.

### Recent Activity

Returns at most six real `AuditLog` records where `action` starts with
`platform.`, newest first. Safe output includes action, entity identifiers,
mapped description, actor ID/name, category, and timestamp. Before/after JSON,
request metadata, contact information, tokens, and secrets are never returned.
Unknown platform actions receive a neutral description derived only from the
action name; no event is fabricated when the table is empty.

## Reconciliation Rules

- Dashboard total, active, and suspended library counts equal the corresponding
  platform-library list totals.
- Dashboard total owners equals active-owner plus suspended-owner list totals;
  invitation rows are reconciled separately through `invitedOwners`.
- Dashboard students equal a distinct source query over eligible Student rows.
- Library-status distribution sums to total libraries.
- Top-library counts use isolated correlated aggregates so students, seats,
  allocations, and memberships cannot multiply one another.

## Index And Persistence Decision

No dashboard counters are stored and no speculative indexes are added. Existing
status, role, library foreign-key, allocation-conflict, and audit-action indexes
are used first. PostgreSQL performance and plan tests capture query count,
elapsed time, response size, and representative `EXPLAIN` output; an index will
be proposed only if that profiling demonstrates a real bottleneck.
