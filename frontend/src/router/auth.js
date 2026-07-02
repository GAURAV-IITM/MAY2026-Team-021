import AuthLayout from '../layouts/AuthLayout.vue'

import Login from '../pages/auth/Login.vue'
import RegisterLibrary from '../pages/auth/RegisterLibrary.vue'
import ForgotPassword from '../pages/auth/ForgotPassword.vue'

// Auth route module.
// TODO: Apply guest-only navigation behavior after authentication is implemented.
const authRoutes = [
  {
    path: '/',
    component: AuthLayout,
    meta: { title: 'Authentication', requiresAuth: false, guestOnly: true },
    children: [
      {
        path: '',
        redirect: { name: 'login' },
        meta: { title: 'Authentication', requiresAuth: false, guestOnly: true },
      },
      {
        path: 'login',
        name: 'login',
        component: Login,
        meta: { title: 'Login', requiresAuth: false, guestOnly: true },
      },
      {
        path: 'register-library',
        name: 'registerLibrary',
        component: RegisterLibrary,
        meta: { title: 'Register Library', requiresAuth: false, guestOnly: true },
      },
      {
        path: 'forgot-password',
        name: 'forgotPassword',
        component: ForgotPassword,
        meta: { title: 'Forgot Password', requiresAuth: false, guestOnly: true },
      },
    ],
  },
]

export default authRoutes
