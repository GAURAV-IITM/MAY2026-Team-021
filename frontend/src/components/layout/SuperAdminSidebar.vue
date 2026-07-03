<template>
  <aside
    id="super-admin-sidebar"
    class="app-sidebar super-admin-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Super Admin sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo">SLA</span>
      <span class="app-sidebar__title">Platform</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Super Admin menu">
      <ul>
        <li v-for="item in menuItems" :key="item.routeName">
          <RouterLink
            class="app-sidebar__link"
            :to="{ name: item.routeName }"
            @click="$emit('close')"
          >
            <span class="app-sidebar__marker" aria-hidden="true"></span>
            <span class="app-sidebar__label">{{ item.label }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </aside>

  <button
    v-if="isOpen"
    class="app-sidebar__backdrop"
    type="button"
    aria-label="Close super admin sidebar"
    @click="$emit('close')"
  ></button>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
  isOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

const menuItems = [
  { label: 'Dashboard', routeName: 'superAdminDashboard' },
  { label: 'Libraries', routeName: 'superAdminLibraries' },
  { label: 'Owners', routeName: 'superAdminOwners' },
  { label: 'Subscriptions', routeName: 'superAdminSubscriptions' },
  { label: 'Analytics', routeName: 'superAdminAnalytics' },
  { label: 'Settings', routeName: 'superAdminSettings' },
]
</script>

<!--
TODO:
- Replace placeholder markers with final icons when the icon system is selected.
- Connect menu visibility to platform permissions when guards are implemented.
-->
