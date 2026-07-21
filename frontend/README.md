# Smart Library App Frontend

The frontend for **Smart Library App**, a role-based library operations platform built for library owners, students, and platform administrators.

The application currently uses mock services and local frontend state so the complete user experience can be developed independently of the backend. The service layer is intentionally separated from pages and stores to support a later FastAPI integration with minimal UI changes.

## Application Areas

### Library Owner

- Operational dashboard
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
| Axios                  | HTTP client scaffold for backend API integration         |
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
npm run dev
```

Vite prints the local development URL in the terminal, normally `http://localhost:5173`.

No environment variables or running backend are required for the current mock-service implementation.

## Demo Accounts

Use these accounts on the login page to open each role-specific portal:

| Role          | Email                          | Password      |
| ------------- | ------------------------------ | ------------- |
| Library Owner | `owner@smartlibrary.test`      | `Owner@123`   |
| Student       | `student@smartlibrary.test`    | `Student@123` |
| Super Admin   | `superadmin@smartlibrary.test` | `Super@123`   |

These credentials are development-only mock data and must not be used in production.

## Available Scripts

```bash
npm run dev       # Start the Vite development server
npm run build     # Create a production build in dist/
npm run preview   # Preview the production build locally
npm run lint      # Run ESLint across the frontend
npm run format    # Format supported files with Prettier
```

Before opening a pull request, run:

```bash
npm run lint
npm run build
```

An automated test command is not configured yet.

## Architecture

Feature data follows this flow:

```text
Page / Component
      ↓
Pinia Store
      ↓
Feature Service
      ↓
Mock Data (current) or HTTP API (future)
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
│   ├── api/                Shared Axios client and future API adapters
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

- Authentication uses mock users and a fake session token stored in `localStorage`.
- Most feature services work with in-memory mock data and may reset after a browser refresh.
- Library registration creates a mock owner session and initializes the requested number of seats.
- Mock delays are used in several services to exercise loading and error UI.
- Tenant isolation and permissions are represented in the frontend but must be enforced by the backend before production use.

Mock files are located in `src/mocks/`; pages must access them through their corresponding service and store.

## Backend Integration

The shared Axios client is available at `src/api/axios.js` with `/api` as its current base URL. Backend integration should preserve the existing store contracts where possible.

When connecting FastAPI:

1. Replace mock operations inside feature services with Axios requests.
2. Move authentication from fake local storage tokens to backend-issued secure tokens or sessions.
3. Add authentication headers and centralized request/response interceptors.
4. Enforce roles, library tenancy, validation, and conflict rules on the backend.
5. Add environment-based API configuration and automated tests.

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
