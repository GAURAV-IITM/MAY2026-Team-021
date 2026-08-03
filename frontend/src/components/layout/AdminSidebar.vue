<template>
  <aside
    id="admin-sidebar"
    class="app-sidebar admin-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Admin sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo" aria-hidden="true"><LibraryBig :size="22" /></span>
      <span class="app-sidebar__title">Admin</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Admin menu">
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
    aria-label="Close admin sidebar"
    @click="$emit('close')"
  ></button>
</template>

<script setup>
import {
  Armchair,
  BarChart3,
  ClipboardList,
  Clock3,
  CreditCard,
  LayoutDashboard,
  LibraryBig,
  ListChecks,
  Map,
  Megaphone,
  ReceiptText,
  Settings,
  UserRound,
  UsersRound,
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
  { label: 'Dashboard', routeName: 'adminDashboard', icon: LayoutDashboard },
  { label: 'Students', routeName: 'adminStudents', icon: UsersRound },
  { label: 'Seat Requests', routeName: 'adminSeatRequests', icon: ClipboardList },
  { label: 'Seat Map', routeName: 'adminSeatMap', icon: Map },
  { label: 'Allocations', routeName: 'adminSeatAllocations', icon: ListChecks },
  { label: 'Seat Management', routeName: 'adminSeatManagement', icon: Armchair },
  { label: 'Shift Management', routeName: 'adminShiftManagement', icon: Clock3 },
  { label: 'Payments', routeName: 'adminPayments', icon: CreditCard },
  { label: 'Receipts', routeName: 'adminReceipts', icon: ReceiptText },
  { label: 'Reports & Analytics', routeName: 'adminReports', icon: BarChart3 },
  { label: 'Announcements', routeName: 'adminAnnouncements', icon: Megaphone },
  { label: 'My Profile', routeName: 'adminProfile', icon: UserRound },
  { label: 'Settings', routeName: 'adminSettings', icon: Settings },
]
</script>

<!--
TODO: Connect menu visibility to role and tenant permissions when guards are implemented.
-->
