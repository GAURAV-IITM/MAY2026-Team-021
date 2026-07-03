<template>
  <header class="app-navbar student-navbar">
    <div class="app-navbar__brand">
      <button
        class="app-navbar__menu-button"
        type="button"
        :aria-expanded="String(isSidebarOpen)"
        aria-controls="student-sidebar"
        aria-label="Toggle student sidebar"
        @click="$emit('toggleSidebar')"
      >
        <span aria-hidden="true">☰</span>
      </button>
      <span class="app-navbar__logo">Smart Library App</span>
    </div>

    <div class="app-navbar__page">
      <p class="app-navbar__breadcrumb">Student / {{ pageTitle }}</p>
      <h1>{{ pageTitle }}</h1>
    </div>

    <div class="app-navbar__actions" aria-label="Student toolbar">
      <label class="app-navbar__search">
        <span class="sr-only">Search</span>
        <input type="search" placeholder="Search" />
      </label>
      <button class="app-navbar__icon-button" type="button" aria-label="Notifications">N</button>
      <span class="app-navbar__library">Library Placeholder</span>
      <button class="app-navbar__profile" type="button">Student User</button>
      <button class="app-navbar__logout" type="button">Logout</button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
  isSidebarOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggleSidebar'])

const route = useRoute()
const pageTitle = computed(() => route.meta.title || 'Dashboard')
</script>

<!--
TODO:
- Add student account navigation after authentication is implemented.
- Wire search, notifications, profile menu, and logout after backend/auth integration.
-->
