<template>
  <header class="auth-navbar">
    <RouterLink class="auth-navbar__logo" :to="{ name: 'landing' }">
      <LibraryBig :size="20" aria-hidden="true" /> Smart Library App
    </RouterLink>
  </header>
</template>

<script setup>
import { LibraryBig } from '@lucide/vue'
import { RouterLink } from 'vue-router'
</script>
