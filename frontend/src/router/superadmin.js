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
    children: [
      { path: '', redirect: { name: 'superAdminDashboard' } },
      { path: 'dashboard', name: 'superAdminDashboard', component: SuperAdminDashboard },
      { path: 'libraries', name: 'superAdminLibraries', component: SuperAdminLibraries },
      { path: 'owners', name: 'superAdminOwners', component: SuperAdminOwners },
      {
        path: 'subscriptions',
        name: 'superAdminSubscriptions',
        component: SuperAdminSubscriptions,
      },
      { path: 'analytics', name: 'superAdminAnalytics', component: SuperAdminAnalytics },
      { path: 'settings', name: 'superAdminSettings', component: SuperAdminSettings },
    ],
  },
]

export default superAdminRoutes
