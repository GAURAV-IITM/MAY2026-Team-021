import AuthLayout from '../layouts/AuthLayout.vue'
import PublicLayout from '../layouts/PublicLayout.vue'

import LandingPage from '../pages/public/LandingPage.vue'
import Login from '../pages/auth/Login.vue'
import RegisterLibrary from '../pages/auth/RegisterLibrary.vue'
import ForgotPassword from '../pages/auth/ForgotPassword.vue'

// Auth & Public route module.
// Public pages are accessible without authentication.
// Authentication pages remain guest-only.
const authRoutes = [
  // Public Routes
  {
    path: '/',
    component: PublicLayout,
    meta: { title: 'Home', requiresAuth: false, },
    children: [
      {
        path: '',
        name: 'landing',
        component: LandingPage,
        meta: { title: 'Study Spaces', requiresAuth: false, },
      },
    ],
  },

  // Authentication Routes
  {
    path: '/',
    component: AuthLayout,
    meta: { title: 'Authentication', requiresAuth: false, },
    children: [
      {
        path: 'login',
        name: 'login',
        component: Login,
        meta: { title: 'Login', requiresAuth: false, guestOnly: true, },
      },
      {
        path: 'register-library',
        name: 'registerLibrary',
        component: RegisterLibrary,
        meta: { title: 'Register Library', requiresAuth: false, guestOnly: true, },
      },
      {
        path: 'forgot-password',
        name: 'forgotPassword',
        component: ForgotPassword,
        meta: { title: 'Forgot Password', requiresAuth: false, guestOnly: true, },
      },
    ],
  },
]

export default authRoutes