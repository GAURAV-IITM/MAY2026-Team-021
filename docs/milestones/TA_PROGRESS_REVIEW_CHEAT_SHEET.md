# TA Progress Review Cheat Sheet

## Opening

> Milestone 1 identified manual seat conflicts, fee tracking, and fragmented records.
> Milestone 2 established our Vue and layered architecture. Milestone 3 API Sprint 1,
> which continues as Project Sprint 7, implements the real backend for the main owner
> and student workflows.

## Three numbers

- **74** documented FastAPI operations
- **133** tests passing in today's local backend run
- **12** Swagger API groups

## Show in this order

1. Swagger `/docs` and `GET /health`
2. Library registration with automatic floor, shifts, and seats
3. Invalid `seatCount: 0` returning structured `422`
4. Overnight shift overlap or seat-allocation conflict
5. Partial payment -> final payment -> receipt
6. Four targeted pytest cases
7. OpenAPI drift check
8. Next-sprint plan

## Live test command

```bash
cd backend
source venv/bin/activate
pytest -vv \
  tests/test_auth_api.py::test_registration_bootstraps_library_and_me \
  tests/test_core_library_api.py::test_floor_seat_shift_and_settings_workflows \
  tests/test_seat_allocation_api.py::test_conflicts_atomicity_status_precedence_and_consecutive_dates \
  tests/test_payment_api.py::test_partial_and_full_payments_recalculate_server_totals
```

Expected: `4 passed` in roughly three seconds.

## Strong design points

- Tenant is derived from authenticated membership, not client input.
- JWTs are backed by revocable, rotating server-side sessions.
- Seat availability is calculated for shift plus date range.
- Transactions and history are retained; multi-step failures roll back.
- Payments support instalments because fee records and transactions are separate.
- Swagger is generated and checked against FastAPI to prevent contract drift.

## Failed test story

`GET /api/v1/auth/me` initially returned `200` for a valid JWT whose database session
had already expired. Expected result was `401`. We added backing-session validation and
a regression test; it now returns `401`.

## Next sprint

1. Complete real Super Admin APIs and frontend integration.
2. Capture production-like concurrency and report-performance evidence.
3. Expand audit coverage and required background workflows.
4. Conduct external owner/student UAT and document feedback.
5. Complete deployment, security, migration, and Milestone 4 preparation.

## Do not overclaim

- Say `133 passing tests`; do not say all 140 tests ran locally.
- Say core owner/student modules use real APIs; Super Admin still has mock-backed areas.
- Say external post-demonstration feedback is pending until it is actually collected.
- Do not call calculated seat availability a stored physical seat status.

## Ask the TA

1. Must post-demo feedback come from the original interviewee?
2. Is production-like concurrency evidence required in CI or acceptable as a documented run?
3. Is `x-user-stories` acceptable for Swagger user-story mapping?
4. Should this be labelled Project Sprint 7 for continuity?

## Closing

> We have moved the main owner and student workflows from mocks to 74 documented,
> tenant-scoped APIs. Today's backend run has 133 passing tests. The next sprint closes
> the remaining Super Admin, production-database, UAT, and deployment work.
