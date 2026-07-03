<template>
  <aside
    id="student-sidebar"
    class="app-sidebar student-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Student sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo">SLA</span>
      <span class="app-sidebar__title">Student</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Student menu">
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
    aria-label="Close student sidebar"
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
  { label: 'Dashboard', routeName: 'studentDashboard' },
  { label: 'My Seat', routeName: 'studentMySeat' },
  { label: 'Fees', routeName: 'studentFees' },
  { label: 'Receipts', routeName: 'studentReceipts' },
  { label: 'Requests', routeName: 'studentRequests' },
  { label: 'Announcements', routeName: 'studentAnnouncements' },
  { label: 'Profile', routeName: 'studentProfile' },
]
</script>

<!--
TODO:
- Replace placeholder markers with final icons when the icon system is selected.
- Connect menu visibility to student account permissions when guards are implemented.
-->
