import { createRouter, createWebHistory } from 'vue-router'

import authRoutes from './auth'
import adminRoutes from './admin'
import studentRoutes from './student'
import superAdminRoutes from './superadmin'

import BlankLayout from '../layouts/BlankLayout.vue'
import NotFound from '../pages/shared/NotFound.vue'

// src/router: Central route composition and future navigation guard registration.
// TODO: Register the Authentication Guard here after JWT authentication is implemented.
// TODO: Register the Role Guard here after role validation rules are finalized.
// TODO: Register the Tenant Guard here after tenant validation is available from the backend.
// TODO: Navigation guards should read route meta and delegate checks to guards/*.js.
const routes = [
  ...authRoutes,
  ...adminRoutes,
  ...studentRoutes,
  ...superAdminRoutes,
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

export default router
