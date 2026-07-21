<template>
  <aside
    id="admin-sidebar"
    class="app-sidebar admin-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Admin sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo">SLA</span>
      <span class="app-sidebar__title">Admin</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Admin menu">
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
    aria-label="Close admin sidebar"
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
  { label: 'Dashboard', routeName: 'adminDashboard' },
  { label: 'Students', routeName: 'adminStudents' },
  { label: 'Seat Requests', routeName: 'adminSeatRequests' },
  { label: 'Seat Map', routeName: 'adminSeatMap' },
  { label: 'Seat Management', routeName: 'adminSeatManagement' },
  { label: 'Shift Management', routeName: 'adminShiftManagement' },
  { label: 'Payments', routeName: 'adminPayments' },
  { label: 'Receipts', routeName: 'adminReceipts' },
  { label: 'Reports & Analytics', routeName: 'adminReports' },
  { label: 'Announcements', routeName: 'adminAnnouncements' },
  { label: 'Settings', routeName: 'adminSettings' },
]
</script>

<!--
TODO:
- Replace placeholder markers with final icons when the icon system is selected.
- Connect menu visibility to role and tenant permissions when guards are implemented.
-->
