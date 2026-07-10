// Error route module.
// Handles application error pages and undefined routes.

import PublicLayout from '../layouts/PublicLayout.vue'

import NotFound from '../pages/errors/NotFound.vue'
import Unauthorized from '../pages/errors/Unauthorized.vue'
import Forbidden from '../pages/errors/Forbidden.vue'
import ServerError from '../pages/errors/ServerError.vue'

const errorRoutes = [
  {
    path: '/',
    component: PublicLayout,
    meta: {
      title: 'Error',
      requiresAuth: false,
    },
    children: [
      {
        path: '401',
        name: 'unauthorized',
        component: Unauthorized,
        meta: {
          title: 'Unauthorized',
          requiresAuth: false,
        },
      },
      {
        path: '403',
        name: 'forbidden',
        component: Forbidden,
        meta: {
          title: 'Forbidden',
          requiresAuth: false,
        },
      },
      {
        path: '500',
        name: 'serverError',
        component: ServerError,
        meta: {
          title: 'Server Error',
          requiresAuth: false,
        },
      },
      {
        path: ':pathMatch(.*)*',
        name: 'notFound',
        component: NotFound,
        meta: {
          title: 'Page Not Found',
          requiresAuth: false,
        },
      },
    ],
  },
]

export default errorRoutes