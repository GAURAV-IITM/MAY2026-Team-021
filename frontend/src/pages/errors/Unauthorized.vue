<template>
  <ErrorPage
    code="401"
    title="Unauthorized"
    description="Please sign in to access this page."
  />
</template>

<script setup>
import ErrorPage from '../../components/errors/ErrorPage.vue'
</script>