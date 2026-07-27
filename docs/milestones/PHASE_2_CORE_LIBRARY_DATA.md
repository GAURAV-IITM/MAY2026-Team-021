# Phase 2: Core Library Data

Status: Implemented  
Target: 26-28 July 2026

## Goal

Move student profiles, floors, physical seats, shifts, and library settings
from frontend mocks to tenant-scoped FastAPI endpoints. Seat allocations,
monthly fee records, and audit logging remain in their planned later phases.

## Architecture

Each connected frontend flow follows:

```text
Vue page/component -> Pinia store -> Axios service -> FastAPI endpoint
-> domain service -> tenant-scoped repository -> SQLAlchemy model
```

Pages do not import Phase 2 mock data. The backend derives `library_id` from
the authenticated membership and never trusts a client-provided tenant ID.

## Student Management

Implemented:

- paginated list and search;
- create, detail, update, status, and soft-delete operations;
- per-library email and enrollment-number uniqueness;
- generated enrollment numbers when the owner leaves the field blank;
- Active, Inactive, Suspended, and Left lifecycle states;
- expiring student portal invitations and password setup.

Student creation manages profile data and the monthly fee preference. Seat
allocation and generated fee records are intentionally not part of this form.

### Invitation Flow

1. Owner creates a student with `sendInvitation: true` or requests a new link.
2. Backend revokes any previous pending link.
3. Backend returns a one-time setup URL and stores only the token hash.
4. Student opens `/accept-invitation?token=...`.
5. Backend validates the pending, unexpired token.
6. Student chooses a password.
7. Backend creates the Student role, user, active membership, and links the
   student profile in one transaction.
8. Reusing the token is rejected.

Email delivery is not implemented in this phase. The owner can copy the setup
link from Student Details and share it through the library's chosen channel.

## Floors And Seats

Floor CRUD is available from the Manage Floors action on Seat Management.
Seat create/edit forms select an active floor by ID.

Physical seat states are Available, Maintenance, and Blocked. Occupied and
Reserved are derived from allocations; they are not saved as physical seat
states. Bulk status and delete operations are transactional. Floors containing
seats and seats with active or future allocations cannot be deleted.

## Shifts

Shift CRUD supports same-day and overnight time ranges. A start time equal to
the end time is invalid.

Overlapping definitions are allowed because a library may need Morning,
Office Hours, and other custom windows at the same time. Workflows selecting
multiple shifts call `/shifts/validate-selection`.

```text
Overnight: 22:00 -> 02:00
Early:     01:00 -> 06:00
Result: invalid selection, overlap from 01:00 to 02:00
```

Adjacent windows such as `06:00 -> 12:00` and `12:00 -> 18:00` do not overlap.

## Library Settings

The owner settings page now reads and writes the real library and
`library_settings` rows, including contact details, operating hours, fee
defaults, receipt rules, and notification preferences.

## Verification

Backend:

```bash
cd backend
python scripts/export_openapi.py
python scripts/export_openapi.py --check
pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
```

Focused tests cover tenant isolation, invitation activation and reuse, status
effects, floor and seat CRUD, bulk status changes, overnight overlap, and
settings persistence.

## Deferred Work

- Seat allocation, transfer, and full date-range availability: Phase 3.
- Monthly fee generation and payment records: payment phase.
- Email/SMS invitation delivery: notification integration.
- Mutation audit records: audit phase.
