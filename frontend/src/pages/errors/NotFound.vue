<template>
  <ErrorPage
    code="404"
    title="Page Not Found"
    description="The page you are looking for does not exist or may have been moved."
    :actions="actions"
  />
</template>

<script setup>
import ErrorPage from '../../components/errors/ErrorPage.vue'

const actions = [
  { label: 'Go Home', to: { name: 'landing' }, variant: 'primary' },
  { label: 'Go Back', action: 'back', variant: 'secondary' },
]
</script>
