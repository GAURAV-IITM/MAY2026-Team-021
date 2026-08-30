# MAY2026-Team-021

## Library Management System

### Team Members

1. Shubham Nagar
2. Gaurav Ghodge
3. Hitarth mehta
4. Piyush Jha
5. MANDEEP

## Project Description

A web-based Library Management System that helps manage seats, shifts, users,
payments, reminders, announcements, and reports.

## Implementation Plan

The shared team plan for API development, testing, frontend integration, user
feedback, and Milestone 3 and 4 submissions is available at
[`docs/milestones/MILESTONE_3_4_IMPLEMENTATION_PLAN.md`](docs/milestones/MILESTONE_3_4_IMPLEMENTATION_PLAN.md).

## Tech Stack

- Frontend: Vue 3
- Backend: FastAPI
- Database: SQLite for local development; PostgreSQL-compatible configuration for shared and concurrency testing
- Version control: GitHub

## Running the Project

The application has two parts: a FastAPI backend and a Vue/Vite frontend. Start
the backend first, then start the frontend in a second terminal.

### Prerequisites

- Python 3.12 or a compatible Python 3 version
- Node.js `20.19+` or `22.12+`
- npm

The default development database is SQLite, so PostgreSQL is not required for
the basic local setup. PostgreSQL can be configured later through
`backend/.env` when database concurrency or performance tests are needed.

### 1. Start the backend

From the repository root, run:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `backend/.env` and replace the placeholder `JWT_SECRET_KEY` with a unique
random value of at least 32 characters. Then apply the database migrations and
start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The backend will be available at:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>

The default backend configuration uses SQLite and creates the local database
at `backend/smart_library.db`. To use PostgreSQL instead, set `DATABASE_URL`
in `backend/.env` to a PostgreSQL connection string.

### 2. Start the frontend

Open a second terminal at the repository root and run:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Vite normally serves the frontend at <http://localhost:5173>. The frontend
expects the backend at `http://localhost:8000` by default. This can be changed
with `VITE_API_PROXY_TARGET` or `VITE_API_BASE_URL` in `frontend/.env`.

With both servers running, open <http://localhost:5173> in a browser. Library
owners can create an account from `/register-library`; users can sign in from
`/login`.

### 3. Run the checks

Run the backend checks from the `backend/` directory with the virtual
environment activated:

```bash
pytest
python scripts/export_openapi.py --check
```

Run the frontend checks from the `frontend/` directory:

```bash
npm test
npm run lint
npm run build
```

### Useful database commands

Run these commands from `backend/` with the virtual environment activated:

```bash
alembic upgrade head       # Apply all migrations
alembic downgrade -1       # Roll back the latest migration
```

Alembic owns the database schema. The application should be started with the
migrations applied; it does not create the schema automatically at startup.

For more detailed backend and frontend information, see
[`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md).
