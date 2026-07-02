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
    children: [
      { path: '', redirect: { name: 'login' } },
      { path: 'login', name: 'login', component: Login },
      { path: 'register-library', name: 'registerLibrary', component: RegisterLibrary },
      { path: 'forgot-password', name: 'forgotPassword', component: ForgotPassword },
    ],
  },
]

export default authRoutes
