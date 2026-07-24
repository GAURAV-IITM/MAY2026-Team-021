<template>
  <ErrorPage
    code="401"
    title="Unauthorized"
    description="Please sign in to access this page."
    :actions="actions"
  />
</template>

<script setup>
import ErrorPage from '../../components/errors/ErrorPage.vue'

const actions = [
  { label: 'Login', to: { name: 'login' }, variant: 'primary' },
  { label: 'Go Home', to: { name: 'landing' }, variant: 'secondary' },
]
</script>
