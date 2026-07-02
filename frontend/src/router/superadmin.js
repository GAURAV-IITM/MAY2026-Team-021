import SuperAdminLayout from '../layouts/SuperAdminLayout.vue'

import SuperAdminDashboard from '../pages/superadmin/Dashboard.vue'
import SuperAdminLibraries from '../pages/superadmin/Libraries.vue'
import SuperAdminOwners from '../pages/superadmin/Owners.vue'
import SuperAdminSubscriptions from '../pages/superadmin/Subscriptions.vue'
import SuperAdminAnalytics from '../pages/superadmin/Analytics.vue'
import SuperAdminSettings from '../pages/superadmin/Settings.vue'

// Super Admin route module.
// TODO: Attach platform-level guards after authentication and permissions are implemented.
const superAdminRoutes = [
  {
    path: '/superadmin',
    component: SuperAdminLayout,
    meta: { title: 'Super Admin', role: 'superadmin', requiresAuth: true },
    children: [
      {
        path: '',
        redirect: { name: 'superAdminDashboard' },
        meta: { title: 'Super Admin', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'dashboard',
        name: 'superAdminDashboard',
        component: SuperAdminDashboard,
        meta: { title: 'Dashboard', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'libraries',
        name: 'superAdminLibraries',
        component: SuperAdminLibraries,
        meta: { title: 'Libraries', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'owners',
        name: 'superAdminOwners',
        component: SuperAdminOwners,
        meta: { title: 'Owners', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'subscriptions',
        name: 'superAdminSubscriptions',
        component: SuperAdminSubscriptions,
        meta: { title: 'Subscriptions', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'analytics',
        name: 'superAdminAnalytics',
        component: SuperAdminAnalytics,
        meta: { title: 'Analytics', role: 'superadmin', requiresAuth: true },
      },
      {
        path: 'settings',
        name: 'superAdminSettings',
        component: SuperAdminSettings,
        meta: { title: 'Settings', role: 'superadmin', requiresAuth: true },
      },
    ],
  },
]

export default superAdminRoutes
