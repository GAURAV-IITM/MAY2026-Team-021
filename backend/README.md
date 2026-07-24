# Smart Library Backend

FastAPI and SQLAlchemy foundation for the Smart Library application. The
current backend includes the database models, Alembic migrations, and module
boundaries required by the completed frontend. API use cases are intentionally
left as placeholders for Milestone 3.

## Setup

From `backend/`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The default development database is SQLite. PostgreSQL URLs in the common
`postgresql://user:password@host/database` format are automatically configured
to use the bundled Psycopg 3 binary driver, so local compiler and PostgreSQL
header packages are not required.

## Structure

```text
app/
  api/           FastAPI routes and dependencies
  core/          Configuration, security, and shared exceptions
  db/            SQLAlchemy base/session and Alembic migrations
  models/        Persistent domain entities
  repositories/  Tenant-scoped database access
  schemas/       Pydantic API contracts
  services/      Business rules and transaction boundaries
  tasks/         Scheduled and background job entry points
docs/            Revised ERD and database business rules
tests/           Database and application smoke tests
```

## Database commands

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe the change"
```

Never call `Base.metadata.create_all()` from application startup. Alembic owns
schema creation and upgrades.

## Important design choices

- Every library-owned business record carries a `library_id` for tenant scope.
- Seat rows store only physical state: available, maintenance, or blocked.
- Allotted, reserved, and blocked-by-another-shift are calculated from dated
  seat allocations for the requested shift window.
- Allocations, payments, receipts, status changes, and audit records are kept
  as history rather than overwritten or hard-deleted.
- Monthly fee records are separate from payment transactions, allowing partial
  payments and immutable receipts.
- Reports and dashboard totals are query results, not duplicated source data.

See [docs/ERD.md](docs/ERD.md) and
[docs/DATABASE_RULES.md](docs/DATABASE_RULES.md) for the complete model.
