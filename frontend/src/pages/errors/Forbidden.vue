<template>
  <ErrorPage
    code="403"
    title="Access Forbidden"
    description="You don't have permission to access this resource."
    :actions="actions"
  />
</template>

<script setup>
import { computed } from 'vue'

import ErrorPage from '../../components/errors/ErrorPage.vue'
import { getDashboardRouteForRole } from '../../guards/authGuard'
import { useAuthStore } from '../../stores/authStore'

const authStore = useAuthStore()
const actions = computed(() => {
  const dashboardRoute = getDashboardRouteForRole(authStore.currentRole)
  const hasDashboard = dashboardRoute !== 'login'

  return [
    {
      label: hasDashboard ? 'Go to Dashboard' : 'Login',
      to: { name: dashboardRoute },
      variant: 'primary',
    },
    { label: 'Go Home', to: { name: 'landing' }, variant: 'secondary' },
  ]
})
</script>
