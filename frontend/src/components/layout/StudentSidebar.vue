<template>
  <aside
    id="student-sidebar"
    class="app-sidebar student-sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': isOpen }"
    aria-label="Student sidebar"
  >
    <div class="app-sidebar__header">
      <span class="app-sidebar__logo" aria-hidden="true"><LibraryBig :size="22" /></span>
      <span class="app-sidebar__title">Student</span>
    </div>

    <nav class="app-sidebar__nav" aria-label="Student menu">
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
    aria-label="Close student sidebar"
    @click="$emit('close')"
  ></button>
</template>

<script setup>
import {
  Armchair,
  ClipboardList,
  LayoutDashboard,
  LibraryBig,
  Megaphone,
  ReceiptText,
  UserRound,
  WalletCards,
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
  { label: 'Dashboard', routeName: 'studentDashboard', icon: LayoutDashboard },
  { label: 'My Seat', routeName: 'studentMySeat', icon: Armchair },
  { label: 'Fees', routeName: 'studentFees', icon: WalletCards },
  { label: 'Receipts', routeName: 'studentReceipts', icon: ReceiptText },
  { label: 'Requests', routeName: 'studentRequests', icon: ClipboardList },
  { label: 'Announcements', routeName: 'studentAnnouncements', icon: Megaphone },
  { label: 'Profile', routeName: 'studentProfile', icon: UserRound },
]
</script>

<!--
TODO: Connect menu visibility to student account permissions when guards are implemented.
-->
