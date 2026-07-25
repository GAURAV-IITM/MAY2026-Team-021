import { createRouter, createWebHistory } from 'vue-router'

import authRoutes from './auth'
import adminRoutes from './admin'
import studentRoutes from './student'
import superAdminRoutes from './superadmin'
import errorRoutes from './errors'

import { ADMIN, STUDENT, SUPER_ADMIN } from '../constants/roles'
import adminGuard from '../guards/adminGuard'
import authGuard, { getRequiredRole } from '../guards/authGuard'
import studentGuard from '../guards/studentGuard'
import superAdminGuard from '../guards/superAdminGuard'

// src/router: Central route composition and future navigation guard registration.
// Authentication and role guards read the backend-validated session from authStore.
// TODO: Register the Tenant Guard here after tenant validation is available from the backend.
// TODO: Replace mock guard behavior with JWT, role claims, and tenant claims from FastAPI.
const routes = [
  ...authRoutes,
  ...adminRoutes,
  ...studentRoutes,
  ...superAdminRoutes,
  ...errorRoutes,
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authResult = await authGuard(to)

  if (authResult !== true) {
    return authResult
  }

  const requiredRole = getRequiredRole(to)

  if (requiredRole === ADMIN) return adminGuard(to)
  if (requiredRole === STUDENT) return studentGuard(to)
  if (requiredRole === SUPER_ADMIN) return superAdminGuard(to)

  return true
})

export default router
