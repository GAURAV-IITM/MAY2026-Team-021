<template>
  <ErrorPage
    code="500"
    title="Internal Server Error"
    description="Something went wrong on our end. Please try again later."
    :actions="actions"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import ErrorPage from '../../components/errors/ErrorPage.vue'

const route = useRoute()
const failedRoute = computed(() => {
  const from = route.query.from

  if (typeof from !== 'string' || !from.startsWith('/') || from.startsWith('//')) {
    return ''
  }

  return from
})
const actions = computed(() => {
  if (!failedRoute.value) {
    return [{ label: 'Go Home', to: { name: 'landing' }, variant: 'primary' }]
  }

  return [
    { label: 'Try Again', to: failedRoute.value, variant: 'primary' },
    { label: 'Go Home', to: { name: 'landing' }, variant: 'secondary' },
  ]
})
</script>
