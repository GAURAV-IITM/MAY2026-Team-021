<template>
  <section class="empty-state" aria-labelledby="unauthorized-title">
    <div class="empty-state__icon" aria-hidden="true"><ShieldAlert :size="26" /></div>
    <h1 id="unauthorized-title" class="text-h4 m-0">Unauthorized</h1>
    <p class="m-0">You do not have permission to view this page.</p>
    <RouterLink class="btn btn--primary" :to="{ name: 'login' }"><LogIn :size="17" aria-hidden="true" /> Back to Login</RouterLink>
  </section>
</template>

<script setup>
import { LogIn, ShieldAlert } from '@lucide/vue'
import { RouterLink } from 'vue-router'
</script>

<!--
src/pages/shared: Legacy unauthorized page retained for compatibility.
-->
