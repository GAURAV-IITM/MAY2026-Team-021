# Owner Report Performance

## Profiling Harness

`backend/tests/test_report_performance_postgres.py` creates an isolated,
temporary PostgreSQL schema and seeds:

- 500 students
- 500 seats across 5 floors
- 6 shifts
- 1,000 active allocations
- 3,000 fee records across 6 months
- 2,000 completed payment transactions
- 1,000 audit records

It measures dashboard and full-report elapsed time, SQL query count, serialized
response size, and `EXPLAIN (ANALYZE, BUFFERS)` plans for fee, allocation, and
recent-audit lookups. The schema is dropped after the test.

Run it only against a disposable test database:

```bash
TEST_POSTGRES_DATABASE_URL=postgresql://... \
  backend/venv/bin/pytest -q -s \
  backend/tests/test_report_performance_postgres.py
```

## Current Run

The test was not executed on 28 July 2026 because
`TEST_POSTGRES_DATABASE_URL` was not configured and no local PostgreSQL server
was available. The normal application `DATABASE_URL` was deliberately not used
for destructive performance seeding.

No report-specific migration or index was added. Existing indexes are retained
until the profiling output provides evidence for a change.
