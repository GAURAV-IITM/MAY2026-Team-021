import { createRouter, createWebHistory } from 'vue-router'

import authRoutes from './auth'
import adminRoutes from './admin'
import studentRoutes from './student'
import superAdminRoutes from './superadmin'

import NotFound from '../pages/shared/NotFound.vue'

// src/router: Central route composition and future navigation guard registration.
// TODO: Add authentication, role, and tenant guards after auth APIs are implemented.
const routes = [
  ...authRoutes,
  ...adminRoutes,
  ...studentRoutes,
  ...superAdminRoutes,
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: NotFound,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
