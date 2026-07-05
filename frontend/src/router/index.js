import { createRouter, createWebHistory } from 'vue-router'

import authRoutes from './auth'
import adminRoutes from './admin'
import studentRoutes from './student'
import superAdminRoutes from './superadmin'

import { ADMIN, STUDENT, SUPER_ADMIN } from '../constants/roles'
import adminGuard from '../guards/adminGuard'
import authGuard, { getRequiredRole } from '../guards/authGuard'
import studentGuard from '../guards/studentGuard'
import superAdminGuard from '../guards/superAdminGuard'
import BlankLayout from '../layouts/BlankLayout.vue'
import NotFound from '../pages/shared/NotFound.vue'
import Unauthorized from '../pages/shared/Unauthorized.vue'

// src/router: Central route composition and future navigation guard registration.
// Authentication Guard is registered below and currently reads the mock session from authStore.
// Role Guard is registered below and currently validates role meta against authStore.currentRole.
// TODO: Register the Tenant Guard here after tenant validation is available from the backend.
// TODO: Replace mock guard behavior with JWT, role claims, and tenant claims from FastAPI.
const routes = [
  ...authRoutes,
  ...adminRoutes,
  ...studentRoutes,
  ...superAdminRoutes,
  {
    path: '/unauthorized',
    component: BlankLayout,
    meta: { title: 'Unauthorized', requiresAuth: true },
    children: [
      {
        path: '',
        name: 'unauthorized',
        component: Unauthorized,
        meta: { title: 'Unauthorized', requiresAuth: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    component: BlankLayout,
    meta: { title: 'Not Found', requiresAuth: false },
    children: [
      {
        path: '',
        name: 'notFound',
        component: NotFound,
        meta: { title: 'Not Found', requiresAuth: false },
      },
    ],
  },
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
