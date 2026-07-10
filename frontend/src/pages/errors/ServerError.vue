<template>
  <ErrorPage
    code="500"
    title="Internal Server Error"
    description="Something went wrong on our end. Please try again later."
  />
</template>

<script setup>
import ErrorPage from '../../components/errors/ErrorPage.vue'
</script>