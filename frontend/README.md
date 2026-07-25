# Smart Library App Frontend

The frontend for **Smart Library App**, a role-based library operations platform built for library owners, students, and platform administrators.

Authentication is integrated with the FastAPI backend. Other feature modules
continue to use mock services until their corresponding APIs are implemented.
The service layer remains separated from pages and stores so each module can be
migrated without rewriting its UI.

## Application Areas

### Library Owner

- Operational dashboard
- Owner account profile and password management
- Student registration and management
- Physical seat management and seat availability map
- Shift management and overlap validation
- Student seat change request review
- Monthly payments, payment history, receipts, and reminders
- Reports and analytics with filters and export controls
- Announcements and library settings

### Student

- Personal dashboard
- Current seat and shift information
- Fee status and receipts
- Seat change requests
- Announcements
- Profile management

### Super Admin

- Platform dashboard
- Library and library-owner management
- Platform analytics
- Platform-wide settings

## Tech Stack

| Technology             | Purpose                                                  |
| ---------------------- | -------------------------------------------------------- |
| Vue 3                  | Component-based user interface using the Composition API |
| Vite 8                 | Development server and production build tooling          |
| Pinia                  | Feature and session state management                     |
| Vue Router             | Public, authenticated, and role-protected navigation     |
| Axios                  | Backend API client with JWT refresh handling             |
| Chart.js / vue-chartjs | Dashboard and report visualizations                      |
| Lucide Vue             | Application icons                                        |
| ESLint / Prettier      | Code quality and formatting                              |

## Prerequisites

- Node.js `20.19+` or `22.12+`
- npm

## Getting Started

From the repository root:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Vite prints the local development URL in the terminal, normally `http://localhost:5173`.

Authentication requires the FastAPI backend, which defaults to
`http://localhost:8000`. Configure another development target with
`VITE_API_PROXY_TARGET`, or set `VITE_API_BASE_URL` when the API is available at
a different public URL.

## Authentication

Library owners can create an account from `/register-library`. All users sign in
through `/login` with backend-managed credentials. Access tokens are kept only
in memory; rotating refresh tokens are stored in Secure, HttpOnly cookies.

## Available Scripts

```bash
npm run dev       # Start the Vite development server
npm run build     # Create a production build in dist/
npm run preview   # Preview the production build locally
npm test          # Run frontend authentication regression tests
npm run lint      # Run ESLint across the frontend
npm run format    # Format supported files with Prettier
```

Before opening a pull request, run:

```bash
npm run lint
npm test
npm run build
```

## Architecture

Feature data follows this flow:

```text
Page / Component
      ↓
Pinia Store
      ↓
Feature Service
      ↓
Backend API or module mock service
```

- **Pages** compose screens and trigger user actions.
- **Components** provide reusable UI and feature-specific building blocks.
- **Stores** own reactive state, loading states, errors, and derived values.
- **Services** contain data access and business rules.
- **Mocks** provide development data until backend endpoints are connected.
- **Guards** enforce authentication and role access at the router level.

Pages should not import mock files directly. Keep data access behind the store and service layers so mock implementations can be replaced by API calls without rewriting views.

## Project Structure

```text
frontend/
├── public/                 Static public assets
├── src/
│   ├── api/                Axios client and authentication session state
│   ├── assets/             Images, logos, icons, and illustrations
│   ├── components/         Shared and feature-level Vue components
│   ├── composables/        Reusable Composition API logic
│   ├── config/             Application and theme configuration
│   ├── constants/          Roles, routes, permissions, and API endpoints
│   ├── guards/             Authentication and role route guards
│   ├── layouts/            Public, auth, owner, student, and admin shells
│   ├── mocks/              Mock datasets used during frontend development
│   ├── pages/              Route-level pages grouped by user role
│   ├── plugins/            Pinia and integration setup helpers
│   ├── router/             Modular route definitions
│   ├── services/           Feature data access and business logic
│   ├── stores/             Pinia feature stores
│   ├── styles/             Global styles, variables, and theme tokens
│   └── utils/              Shared utility functions
├── eslint.config.js
├── vite.config.js
└── package.json
```

## Routes

| Area           | Base route                                        | Access            |
| -------------- | ------------------------------------------------- | ----------------- |
| Landing page   | `/`                                               | Public            |
| Authentication | `/login`, `/register-library`, `/forgot-password` | Guests            |
| Library Owner  | `/admin/*`                                        | `admin` role      |
| Student Portal | `/student/*`                                      | `student` role    |
| Super Admin    | `/superadmin/*`                                   | `superadmin` role |
| Error pages    | `/401`, `/403`, `/500`                            | Public            |

Unknown routes display the dedicated 404 page. Authenticated users are redirected away from guest-only routes, and protected routes validate the active user's role.

## Mock Data Behavior

- Authentication uses the FastAPI JWT and HttpOnly-cookie session endpoints.
- Most feature services work with in-memory mock data and may reset after a browser refresh.
- Library registration creates the owner, library, initial floor, default shifts, and requested seats through the backend.
- Mock delays are used in several services to exercise loading and error UI.
- Tenant isolation and permissions are represented in the frontend but must be enforced by the backend before production use.

Mock files are located in `src/mocks/`; pages must access them through their corresponding service and store.

## Backend Integration

The shared Axios client is available at `src/api/axios.js` with `/api/v1` as its
default base URL. It attaches in-memory access tokens, performs one shared
refresh operation for concurrent unauthorized requests, and retries the
original requests after rotation.

When connecting FastAPI:

1. Replace mock operations inside feature services with Axios requests.
2. Preserve the existing page → store → service boundaries.
3. Enforce roles, library tenancy, validation, and conflict rules on the backend.
4. Add integration tests for each migrated module.

Frontend validation is for usability only. Security-sensitive and business-critical rules must also be validated by the backend.

## Development Guidelines

- Use Vue 3 Composition API and `<script setup>` for new components.
- Reuse components from `src/components/common/` before creating another UI primitive.
- Use Lucide icons for interface actions and navigation.
- Keep route pages focused on orchestration; move shared behavior into stores, services, utilities, or composables.
- Add feature routes to the appropriate module in `src/router/`.
- Use constants instead of repeating role, route, permission, or endpoint strings.
- Preserve responsive behavior for desktop, tablet, and mobile layouts.
- Keep changes scoped and run lint and build checks before submitting them.

## Production Build

```bash
npm run build
npm run preview
```

The optimized build is written to `frontend/dist/`. Configure the deployment server to return `index.html` for unknown application paths so Vue Router history-mode routes work after a direct page load.
