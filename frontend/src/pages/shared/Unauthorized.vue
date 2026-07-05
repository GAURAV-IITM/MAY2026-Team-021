<template>
  <section class="empty-state" aria-labelledby="unauthorized-title">
    <div class="empty-state__icon" aria-hidden="true">!</div>
    <h1 id="unauthorized-title" class="text-h4 m-0">Unauthorized</h1>
    <p class="m-0">You do not have permission to view this page.</p>
    <RouterLink class="btn btn--primary" :to="{ name: 'login' }">Back to Login</RouterLink>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>

<!--
src/pages/shared: Cross-role pages shared by the application shell.
TODO:
- Replace this placeholder with a role-aware unauthorized experience when permissions are finalized.
-->
