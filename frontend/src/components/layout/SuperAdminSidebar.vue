<template>
  <aside
    id="super-admin-sidebar"
    class="app-sidebar super-admin-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Super Admin sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo" aria-hidden="true"><LibraryBig :size="22" /></span>
      <span class="app-sidebar__title">Platform</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Super Admin menu">
      <ul>
        <li v-for="item in menuItems" :key="item.routeName">
          <RouterLink
            class="app-sidebar__link"
            :to="{ name: item.routeName }"
            :title="item.label"
            @click="$emit('close')"
          >
            <component :is="item.icon" class="app-sidebar__icon" :size="19" aria-hidden="true" />
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
import {
  BarChart3,
  Building2,
  LayoutDashboard,
  LibraryBig,
  Settings,
  UserCog,
} from '@lucide/vue'
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
  { label: 'Dashboard', routeName: 'superAdminDashboard', icon: LayoutDashboard },
  { label: 'Libraries', routeName: 'superAdminLibraries', icon: Building2 },
  { label: 'Owners', routeName: 'superAdminOwners', icon: UserCog },
  { label: 'Analytics', routeName: 'superAdminAnalytics', icon: BarChart3 },
  { label: 'Settings', routeName: 'superAdminSettings', icon: Settings },
]
</script>

<!--
TODO: Connect menu visibility to platform permissions when guards are implemented.
-->
