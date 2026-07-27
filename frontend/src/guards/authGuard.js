import { useAuthStore } from '../stores/authStore'

const DASHBOARD_ROUTE_BY_ROLE = Object.freeze({
  admin: 'adminDashboard',
  student: 'studentDashboard',
  superadmin: 'superAdminDashboard',
})

function getRouteMetaValue(to, key) {
  const matchedRoute = [...to.matched].reverse().find((route) => route.meta?.[key] !== undefined)
  return matchedRoute?.meta?.[key]
}

export function getRequiredRole(to) {
  return getRouteMetaValue(to, 'role')
}

export function getDashboardRouteForRole(role) {
  return DASHBOARD_ROUTE_BY_ROLE[role] || 'login'
}

export function ensureRequiredRole(expectedRole) {
  const authStore = useAuthStore()

  if (authStore.currentRole !== expectedRole) {
    return { name: 'forbidden' }
  }

  return true
}

async function ensureAuthState(authStore, to) {
  const needsAuthCheck = Boolean(to.meta.requiresAuth || to.meta.guestOnly)

  if (!needsAuthCheck || authStore.isAuthenticated || authStore.authStatus === 'guest') {
    return
  }

  await authStore.checkSession()
}

// src/guards: Backend-authenticated session and guest-only route checks.
export default async function authGuard(to) {
  const authStore = useAuthStore()

  await ensureAuthState(authStore, to)

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: getDashboardRouteForRole(authStore.currentRole) }
  }

  return true
}
